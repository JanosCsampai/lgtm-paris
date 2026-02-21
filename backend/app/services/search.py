import asyncio
import logging

from langchain_mongodb import MongoDBAtlasVectorSearch

from app.db import get_db, get_sync_db
from app.models.search import (
    MatchedServiceType,
    ObservationSummary,
    ProviderWithPrices,
    SearchResponse,
)
from app.services.discovery import discover_external
from app.services import embeddings as embeddings_svc

logger = logging.getLogger(__name__)

VECTOR_INDEX_NAME = "service_types_vector"
TEXT_INDEX_NAME = "service_types_text"
VECTOR_SCORE_THRESHOLD = 0.75
TEXT_SCORE_THRESHOLD = 0.10


def _get_vector_store() -> MongoDBAtlasVectorSearch | None:
    """Returns None when embeddings are not configured."""
    if not embeddings_svc.is_available():
        return None
    sync_db = get_sync_db()
    return MongoDBAtlasVectorSearch(
        embedding=embeddings_svc.get_embeddings(),
        collection=sync_db.service_types,
        index_name=VECTOR_INDEX_NAME,
        text_key="name",
        embedding_key="embedding",
        relevance_score_fn="cosine",
    )


async def match_service_types_text(query: str) -> list[MatchedServiceType]:
    """Atlas full-text search on service_types (name, slug, category).

    Returns an empty list if the Atlas Search index is unavailable.
    """
    db = get_db()
    pipeline = [
        {
            "$search": {
                "index": TEXT_INDEX_NAME,
                "text": {
                    "query": query,
                    "path": ["name", "slug", "category"],
                    "fuzzy": {"maxEdits": 1},
                },
            }
        },
        {"$addFields": {"score": {"$meta": "searchScore"}}},
        {"$match": {"score": {"$gte": TEXT_SCORE_THRESHOLD}}},
        {"$limit": 10},
        {"$project": {"slug": 1, "name": 1, "score": 1}},
    ]
    results: list[MatchedServiceType] = []
    try:
        async for doc in db.service_types.aggregate(pipeline):
            results.append(
                MatchedServiceType(
                    slug=doc["slug"],
                    name=doc["name"],
                    match_source="text",
                    score=doc["score"],
                )
            )
    except Exception:
        logger.warning("Text search failed — Atlas Search index may not exist", exc_info=True)
    return results


async def match_service_types_vector(query: str) -> list[MatchedServiceType]:
    """Atlas Vector Search — semantic matching on service type embeddings.

    Returns an empty list when embeddings are not configured or the search fails.
    """
    vector_store = _get_vector_store()
    if vector_store is None:
        logger.debug("Vector search skipped — OPENAI_API_KEY not set")
        return []

    try:
        docs_and_scores = await asyncio.to_thread(
            vector_store.similarity_search_with_score, query, k=10
        )
    except Exception:
        logger.warning("Vector search failed — falling back to text-only", exc_info=True)
        return []

    results: list[MatchedServiceType] = []
    for doc, score in docs_and_scores:
        if score < VECTOR_SCORE_THRESHOLD:
            continue
        results.append(
            MatchedServiceType(
                slug=doc.metadata.get("slug", ""),
                name=doc.page_content,
                match_source="vector",
                score=score,
            )
        )
    return results


def _merge_service_types(
    text_matches: list[MatchedServiceType],
    vector_matches: list[MatchedServiceType],
) -> list[MatchedServiceType]:
    """Deduplicate by slug, preferring the higher-scoring match."""
    by_slug: dict[str, MatchedServiceType] = {}
    for m in text_matches + vector_matches:
        existing = by_slug.get(m.slug)
        if existing is None or m.score > existing.score:
            by_slug[m.slug] = m
    return sorted(by_slug.values(), key=lambda m: m.score, reverse=True)


async def find_providers_with_prices(
    service_type_slugs: list[str],
    lat: float,
    lng: float,
    radius_meters: float,
) -> list[ProviderWithPrices]:
    """Geo query on observations, grouped by provider with a $lookup."""
    db = get_db()
    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lng, lat]},
                "distanceField": "distance_meters",
                "maxDistance": radius_meters,
                "query": {"service_type": {"$in": service_type_slugs}},
                "spherical": True,
            }
        },
        {
            "$lookup": {
                "from": "providers",
                "localField": "provider_id",
                "foreignField": "_id",
                "as": "provider",
            }
        },
        {"$unwind": "$provider"},
        {
            "$group": {
                "_id": "$provider_id",
                "provider": {"$first": "$provider"},
                "observations": {
                    "$push": {
                        "service_type": "$service_type",
                        "price": "$price",
                        "currency": "$currency",
                        "source_type": "$source_type",
                        "observed_at": "$observed_at",
                    }
                },
                "distance_meters": {"$first": "$distance_meters"},
            }
        },
        {"$sort": {"distance_meters": 1}},
        {"$limit": 50},
    ]

    results: list[ProviderWithPrices] = []
    async for doc in db.observations.aggregate(pipeline):
        p = doc["provider"]
        results.append(
            ProviderWithPrices(
                id=str(p["_id"]),
                name=p["name"],
                category=p["category"],
                address=p["address"],
                city=p.get("city", ""),
                location=p["location"],
                distance_meters=doc["distance_meters"],
                rating=p.get("rating"),
                review_count=p.get("review_count"),
                description=p.get("description"),
                observations=[ObservationSummary(**o) for o in doc["observations"]],
            )
        )
    return results


async def search(
    query: str,
    lat: float,
    lng: float,
    radius_meters: float,
) -> SearchResponse:
    """Run text + vector search, find nearby providers, trigger discovery if empty."""
    text_matches, vector_matches = await asyncio.gather(
        match_service_types_text(query),
        match_service_types_vector(query),
    )
    merged = _merge_service_types(text_matches, vector_matches)
    slugs = [m.slug for m in merged]

    providers: list[ProviderWithPrices] = []
    if slugs:
        providers = await find_providers_with_prices(slugs, lat, lng, radius_meters)

    discovery_triggered = False
    if not providers:
        discovery_triggered = True
        await discover_external(query, slugs, lat, lng, radius_meters)

    return SearchResponse(
        query=query,
        matched_service_types=merged,
        results=providers,
        discovery_triggered=discovery_triggered,
    )
