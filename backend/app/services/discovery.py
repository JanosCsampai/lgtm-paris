import asyncio
import logging
import math
import re
from datetime import datetime, timezone

from bson import ObjectId
from openai import AsyncOpenAI

from app.config import settings
from app.db import get_db
from app.services import embeddings as embeddings_svc
from app.services.serpapi_service import search_maps

logger = logging.getLogger(__name__)

_EARTH_RADIUS_M = 6_371_000


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two (lat, lng) points."""
    rlat1, rlng1, rlat2, rlng2 = (math.radians(v) for v in (lat1, lng1, lat2, lng2))
    dlat = rlat2 - rlat1
    dlng = rlng2 - rlng1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlng / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(a))


_CONDENSE_PROMPT = (
    "You are a service-type naming assistant. Given a user's free-text search query, "
    "extract a short, canonical service-type name (2-6 words). "
    "Remove filler words like 'I need', 'looking for', 'can someone', etc. "
    "Keep specific product/model identifiers when relevant.\n\n"
    "Examples:\n"
    '  "I need a new screen for my iphone 16 pro max" -> "Screen Repair iPhone 16 Pro Max"\n'
    '  "looking for someone to change oil in my car" -> "Car Oil Change"\n'
    '  "can someone fix my leaky kitchen faucet" -> "Kitchen Faucet Repair"\n'
    '  "best place to get teeth whitening near me" -> "Teeth Whitening"\n\n'
    "Reply with ONLY the service-type name, nothing else."
)


async def condense_query(query: str) -> str:
    """Use the LLM to turn a verbose user query into a short service-type name.

    Falls back to the raw query (title-cased) when OpenAI is unavailable.
    """
    if not settings.openai_api_key:
        return query.strip().title()

    try:
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=30,
            messages=[
                {"role": "system", "content": _CONDENSE_PROMPT},
                {"role": "user", "content": query},
            ],
        )
        name = resp.choices[0].message.content.strip().strip('"')
        logger.info("Condensed query %r -> %r", query, name)
        return name
    except Exception:
        logger.warning("LLM condensation failed, using raw query", exc_info=True)
        return query.strip().title()


def name_to_slug(name: str) -> str:
    slug = name.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug)
    return slug.strip("_")


async def _ensure_service_type(name: str, slug: str) -> str:
    """Return the slug of an existing or newly created service type."""
    db = get_db()

    existing = await db.service_types.find_one({"slug": slug})
    if existing:
        logger.info("Service type '%s' already exists", slug)
        return slug

    category = slug.split("_")[0] if "_" in slug else slug

    doc = {
        "slug": slug,
        "name": name,
        "category": category,
        "description": f"Auto-discovered: {name}",
        "created_at": datetime.now(timezone.utc),
    }

    if embeddings_svc.is_available():
        try:
            text = embeddings_svc.build_search_text(name, category, doc["description"])
            vectors = await asyncio.to_thread(
                embeddings_svc.get_embeddings().embed_documents, [text]
            )
            doc["embedding"] = vectors[0]
        except Exception:
            logger.warning("Failed to generate embedding for %s", slug, exc_info=True)

    await db.service_types.insert_one(doc)
    logger.info("Created service type '%s' (%s)", slug, name)
    return slug


def _business_to_provider_doc(business: dict, category: str) -> dict:
    return {
        "name": business["name"],
        "category": category,
        "location": {
            "type": "Point",
            "coordinates": [business["longitude"], business["latitude"]],
        },
        "address": business.get("address") or "",
        "city": "",
        "rating": business.get("rating"),
        "review_count": business.get("reviews_count"),
        "description": business.get("type"),
        "phone": business.get("phone"),
        "website": business.get("website"),
        "created_at": datetime.now(timezone.utc),
    }


async def discover_external(
    query: str,
    service_type_slugs: list[str],
    lat: float,
    lng: float,
    radius_meters: float,
) -> list[ObjectId]:
    """Find providers via SerpAPI Google Maps and upsert them into MongoDB.

    Returns the list of provider ObjectIds that were upserted/matched.
    """
    if not settings.serpapi_key:
        logger.warning("discover_external skipped — SERPAPI_KEY not configured")
        return []

    if service_type_slugs:
        slug = service_type_slugs[0]
        name = slug.replace("_", " ").title()
    else:
        name = await condense_query(query)
        slug = name_to_slug(name)
    await _ensure_service_type(name, slug)

    try:
        businesses = await search_maps(query, lat, lng, radius_meters)
    except Exception:
        logger.exception("SerpAPI search failed for query=%r", query)
        return []

    if not businesses:
        logger.info("SerpAPI returned no results for query=%r", query)
        return []

    before_count = len(businesses)
    businesses = [
        b for b in businesses
        if _haversine_m(lat, lng, b["latitude"], b["longitude"]) <= radius_meters
    ]
    logger.info(
        "SerpAPI returned %d businesses for query=%r (%d after radius filter)",
        before_count, query, len(businesses),
    )
    if not businesses:
        return []

    db = get_db()
    provider_ids: list[ObjectId] = []
    for biz in businesses:
        if not biz.get("name"):
            continue
        doc = _business_to_provider_doc(biz, slug)
        result = await db.providers.update_one(
            {"name": doc["name"], "address": doc["address"]},
            {"$setOnInsert": doc},
            upsert=True,
        )
        pid = result.upserted_id
        if pid is None:
            existing = await db.providers.find_one(
                {"name": doc["name"], "address": doc["address"]},
                {"_id": 1},
            )
            if existing:
                pid = existing["_id"]
        if pid:
            provider_ids.append(pid)

    logger.info("Upserted up to %d providers for query=%r", len(provider_ids), query)
    return provider_ids
