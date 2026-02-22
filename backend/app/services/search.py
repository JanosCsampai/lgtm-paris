import asyncio
import json
import logging

from bson import ObjectId
from langchain_mongodb import MongoDBAtlasVectorSearch
from openai import AsyncOpenAI

from app.config import settings
from app.db import get_db, get_sync_db
from app.models.search import (
    MatchedServiceType,
    ObservationSummary,
    ProviderWithPrices,
    SearchResponse,
)
from app.services.discovery import discover_external, name_to_slug
from app.services import embeddings as embeddings_svc
from app.services.scraper import scrape_and_store_prices

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


async def find_providers_by_category(
    service_type_slugs: list[str],
    lat: float,
    lng: float,
    radius_meters: float,
) -> list[ProviderWithPrices]:
    """Geo query directly on providers by category (service-type slug).

    Used as a fallback when no observations exist yet — e.g. providers
    were discovered via SerpAPI but have no price observations.
    """
    db = get_db()
    pipeline = [
        {
            "$geoNear": {
                "near": {"type": "Point", "coordinates": [lng, lat]},
                "distanceField": "distance_meters",
                "maxDistance": radius_meters,
                "query": {"category": {"$in": service_type_slugs}},
                "spherical": True,
            }
        },
        {"$sort": {"distance_meters": 1}},
        {"$limit": 50},
    ]

    results: list[ProviderWithPrices] = []
    async for doc in db.providers.aggregate(pipeline):
        results.append(
            ProviderWithPrices(
                id=str(doc["_id"]),
                name=doc["name"],
                category=doc.get("category") or "",
                address=doc.get("address") or "",
                city=doc.get("city") or "",
                location=doc["location"],
                distance_meters=doc.get("distance_meters", 0),
                rating=doc.get("rating"),
                review_count=doc.get("review_count"),
                description=doc.get("description"),
            )
        )
    return results


async def find_providers_by_ids(
    provider_ids: list,
    lat: float,
    lng: float,
    radius_meters: float | None = None,
) -> list[ProviderWithPrices]:
    """Fetch specific providers by ID and compute distance from the search point."""
    if not provider_ids:
        return []
    db = get_db()
    pipeline = [
        {"$match": {"_id": {"$in": provider_ids}}},
        {
            "$addFields": {
                "distance_meters": {
                    "$let": {
                        "vars": {
                            "coords": "$location.coordinates",
                            "refLng": lng,
                            "refLat": lat,
                        },
                        "in": {
                            "$multiply": [
                                6371000,
                                {
                                    "$acos": {
                                        "$min": [
                                            1.0,
                                            {
                                                "$add": [
                                                    {
                                                        "$multiply": [
                                                            {"$sin": {"$degreesToRadians": lat}},
                                                            {"$sin": {"$degreesToRadians": {"$arrayElemAt": ["$$coords", 1]}}},
                                                        ]
                                                    },
                                                    {
                                                        "$multiply": [
                                                            {"$cos": {"$degreesToRadians": lat}},
                                                            {"$cos": {"$degreesToRadians": {"$arrayElemAt": ["$$coords", 1]}}},
                                                            {"$cos": {"$degreesToRadians": {"$subtract": [{"$arrayElemAt": ["$$coords", 0]}, lng]}}},
                                                        ]
                                                    },
                                                ]
                                            },
                                        ]
                                    }
                                },
                            ]
                        },
                    }
                }
            }
        },
        *(
            [{"$match": {"distance_meters": {"$lte": radius_meters}}}]
            if radius_meters is not None
            else []
        ),
        {"$sort": {"distance_meters": 1}},
        {"$limit": 50},
    ]

    results: list[ProviderWithPrices] = []
    async for doc in db.providers.aggregate(pipeline):
        results.append(
            ProviderWithPrices(
                id=str(doc["_id"]),
                name=doc["name"],
                category=doc.get("category") or "",
                address=doc.get("address") or "",
                city=doc.get("city") or "",
                location=doc["location"],
                distance_meters=doc.get("distance_meters", 0),
                rating=doc.get("rating"),
                review_count=doc.get("review_count"),
                description=doc.get("description"),
            )
        )
    return results


_INTENT_PROMPT = (
    "You are a service-type matching assistant. Given a user's search query and a list of "
    "existing service types, you must:\n"
    "1. Extract a short, canonical service-type name (2-6 words) from the query. "
    "Remove filler words. Keep specific product/model identifiers.\n"
    "2. Determine which existing service types (if any) are relevant to this query.\n\n"
    "Matching rules:\n"
    "- Different brands/models/product lines must NOT match "
    "(e.g. iPhone ≠ Galaxy, BMW ≠ Toyota).\n"
    "- Generic types without a specific model (e.g. 'Screen Repair') DO match "
    "any specific query in that category.\n"
    "- Types for the same brand family DO match "
    "(e.g. 'Galaxy Note 10' is relevant for a 'Galaxy' query).\n\n"
    'Reply with ONLY a JSON object: {"name": "<condensed name>", "relevant_slugs": ["slug1", ...]}\n'
    "If no existing types are relevant, return an empty array for relevant_slugs."
)


async def _resolve_intent(
    query: str,
    candidates: list[MatchedServiceType],
) -> tuple[str, list[MatchedServiceType]]:
    """Single LLM call that condenses the query AND validates candidate matches.

    Returns (condensed_name, validated_candidates).
    """
    if not settings.openai_api_key:
        return query.strip().title(), candidates

    slug_map = {m.slug: m for m in candidates}
    if candidates:
        listing = "\n".join(f"- {m.slug}: {m.name}" for m in candidates)
        candidates_block = f"\nExisting service types:\n{listing}"
    else:
        candidates_block = "\nNo existing service types to match against."

    user_msg = f'User query: "{query}"{candidates_block}'

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=200,
            messages=[
                {"role": "system", "content": _INTENT_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )
        content = resp.choices[0].message.content.strip()
        parsed = json.loads(content)
        condensed_name = parsed["name"]
        valid_slugs = set(parsed.get("relevant_slugs", []))
        validated = [slug_map[s] for s in valid_slugs if s in slug_map]
        logger.info(
            "Resolved intent for %r: name=%r, kept %d/%d slugs %s",
            query, condensed_name, len(validated), len(candidates),
            [m.slug for m in validated],
        )
        return condensed_name, validated
    except Exception:
        logger.warning("Intent resolution failed, using raw query", exc_info=True)
        return query.strip().title(), candidates


async def _fetch_provider_docs(provider_ids: list[str]) -> list[dict]:
    """Fetch raw provider documents by ID, including the website field."""
    if not provider_ids:
        return []
    db = get_db()
    oids = [ObjectId(pid) for pid in provider_ids]
    docs = []
    async for doc in db.providers.find({"_id": {"$in": oids}}):
        docs.append(doc)
    return docs


def _providers_needing_scrape(providers: list[ProviderWithPrices]) -> list[str]:
    """Return IDs of providers that have no observations (i.e. no prices yet)."""
    return [p.id for p in providers if not p.observations]


async def _enrich_with_scraped_prices(
    providers: list[ProviderWithPrices],
    query: str,
    service_type_slug: str,
) -> None:
    """Scrape prices for providers missing observations and attach them."""
    ids_to_scrape = _providers_needing_scrape(providers)
    if not ids_to_scrape:
        return

    provider_docs = await _fetch_provider_docs(ids_to_scrape)
    if not provider_docs:
        return

    observations = await scrape_and_store_prices(provider_docs, query, service_type_slug)
    if not observations:
        return

    for p in providers:
        obs = observations.get(p.id)
        if obs:
            p.observations.append(
                ObservationSummary(
                    service_type=obs["service_type"],
                    price=obs["price"],
                    currency=obs["currency"],
                    source_type=obs["source_type"],
                    observed_at=obs["observed_at"],
                )
            )


async def _resolve_category_labels(providers: list[ProviderWithPrices]) -> None:
    """Look up service_types by slug and set category_label on each provider."""
    slugs = list({p.category for p in providers})
    if not slugs:
        return

    db = get_db()
    slug_to_name: dict[str, str] = {}
    async for doc in db.service_types.find({"slug": {"$in": slugs}}, {"slug": 1, "name": 1}):
        slug_to_name[doc["slug"]] = doc["name"]

    for p in providers:
        p.category_label = slug_to_name.get(p.category, p.category.replace("_", " ").title())


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

    condensed_name, validated = await _resolve_intent(query, merged)
    condensed_slug = name_to_slug(condensed_name)

    # Check if the condensed slug exists in DB but wasn't in text/vector results
    validated_slugs = {m.slug for m in validated}
    if condensed_slug not in validated_slugs:
        db = get_db()
        existing = await db.service_types.find_one(
            {"slug": condensed_slug}, {"slug": 1, "name": 1}
        )
        if existing:
            validated.insert(
                0,
                MatchedServiceType(
                    slug=existing["slug"],
                    name=existing["name"],
                    match_source="text",
                    score=1.0,
                ),
            )

    slugs = [m.slug for m in validated]

    providers: list[ProviderWithPrices] = []
    if slugs:
        providers = await find_providers_with_prices(slugs, lat, lng, radius_meters)

    if not providers and slugs:
        providers = await find_providers_by_category(slugs, lat, lng, radius_meters)

    discovery_triggered = False
    if not providers:
        discovered_ids = await discover_external(query, slugs, lat, lng, radius_meters)
        if discovered_ids:
            discovery_triggered = True
            providers = await find_providers_by_ids(discovered_ids, lat, lng, radius_meters)

    if providers:
        primary_slug = slugs[0] if slugs else condensed_slug
        await asyncio.gather(
            _resolve_category_labels(providers),
            _enrich_with_scraped_prices(providers, query, primary_slug),
        )

    return SearchResponse(
        query=query,
        matched_service_types=validated,
        results=providers,
        discovery_triggered=discovery_triggered,
    )
