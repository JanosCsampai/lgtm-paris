from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.provider import GeoJSONPoint


class MatchedServiceType(BaseModel):
    slug: str
    name: str
    match_source: Literal["text", "vector"]
    score: float = Field(description="Search relevance score")


class ObservationSummary(BaseModel):
    service_type: str
    price: float
    currency: str
    source_type: str
    observed_at: datetime


class ProviderWithPrices(BaseModel):
    id: str
    name: str
    category: str
    category_label: str = ""
    address: str
    city: str
    location: GeoJSONPoint
    distance_meters: float
    rating: float | None = None
    review_count: int | None = None
    description: str | None = None
    observations: list[ObservationSummary] = []


class SearchResponse(BaseModel):
    query: str
    matched_service_types: list[MatchedServiceType]
    results: list[ProviderWithPrices]
    discovery_triggered: bool = False
