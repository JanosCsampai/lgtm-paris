import logging

logger = logging.getLogger(__name__)


async def discover_external(
    query: str,
    service_type_slugs: list[str],
    lat: float,
    lng: float,
    radius_meters: float,
) -> None:
    """Trigger external provider/price discovery for a location.

    This is a stub. The implementer should:

    1. **Find providers** — Call the Google Places API (Nearby Search) for
       businesses matching the service category near (lat, lng). Upsert new
       providers into the ``providers`` collection, deduplicating on
       ``google_place_id``.

    2. **Scrape prices** — For each discovered provider, use Linkup (or another
       scraping service) to extract pricing for the requested service types.
       Insert results as observations via ``POST /api/observations`` (or
       directly into the ``observations`` collection with ``source_type="scrape"``).

    3. **Return** — This function is fire-and-forget from the search endpoint's
       perspective. The caller does not wait for results; subsequent searches
       will pick up any newly inserted data.
    """
    logger.info(
        "discover_external triggered (stub) — query=%r service_types=%s "
        "location=(%s, %s) radius=%sm",
        query,
        service_type_slugs,
        lat,
        lng,
        radius_meters,
    )
