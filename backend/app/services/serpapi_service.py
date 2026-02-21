import asyncio
import logging

from serpapi import GoogleSearch

from app.config import settings

logger = logging.getLogger(__name__)

RADIUS_TO_ZOOM = [
    (500, 18),
    (1500, 16),
    (3000, 15),
    (5000, 14),
    (10_000, 13),
    (20_000, 12),
]


def _radius_to_zoom(radius_meters: float) -> int:
    for threshold, zoom in RADIUS_TO_ZOOM:
        if radius_meters <= threshold:
            return zoom
    return 11


def _search_maps_sync(query: str, lat: float, lng: float, zoom: int) -> list[dict]:
    params = {
        "engine": "google_maps",
        "q": query,
        "ll": f"@{lat},{lng},{zoom}z",
        "type": "search",
        "api_key": settings.serpapi_key,
    }

    results = GoogleSearch(params).get_dict()

    businesses = []
    for place in results.get("local_results", []):
        gps = place.get("gps_coordinates", {})
        if not gps.get("latitude") or not gps.get("longitude"):
            continue
        businesses.append({
            "name": place.get("title"),
            "address": place.get("address"),
            "rating": place.get("rating"),
            "reviews_count": place.get("reviews"),
            "phone": place.get("phone"),
            "website": place.get("website"),
            "latitude": gps["latitude"],
            "longitude": gps["longitude"],
            "type": place.get("type"),
            "hours": place.get("hours"),
            "service_options": place.get("service_options", {}),
        })

    return businesses


async def search_maps(
    query: str,
    lat: float,
    lng: float,
    radius_meters: float = 5000,
) -> list[dict]:
    """Search Google Maps via SerpAPI. Runs the blocking HTTP call in a thread."""
    zoom = _radius_to_zoom(radius_meters)
    logger.info(
        "SerpAPI search: query=%r lat=%s lng=%s zoom=%s (radius=%sm)",
        query, lat, lng, zoom, radius_meters,
    )
    return await asyncio.to_thread(_search_maps_sync, query, lat, lng, zoom)
