from fastapi import APIRouter, Query

from app.models.search import SearchResponse
from app.services.search import search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search_services(
    q: str = Query(..., min_length=1, description="Free-text search query"),
    lat: float = Query(..., description="Latitude of the search centre"),
    lng: float = Query(..., description="Longitude of the search centre"),
    radius_meters: float = Query(
        default=5000, gt=0, description="Search radius in metres"
    ),
):
    return await search(q, lat, lng, radius_meters)
