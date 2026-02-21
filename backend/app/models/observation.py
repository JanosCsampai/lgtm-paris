from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.provider import GeoJSONPoint


class ObservationCreate(BaseModel):
    provider_id: str = Field(..., description="ObjectId of the provider")
    service_type: str = Field(..., description="Slug of the service type", examples=["tire_change"])
    price: float = Field(..., gt=0, examples=[45.50])
    currency: str = Field(default="EUR", examples=["EUR", "GBP"])
    source_type: Literal["scrape", "manual", "receipt", "quote"]
    observed_at: Optional[datetime] = Field(
        default=None,
        description="When the price was observed. Defaults to now.",
    )


class ObservationResponse(BaseModel):
    id: str = Field(..., alias="_id")
    provider_id: str
    service_type: str
    category: str
    price: float
    currency: str
    source_type: str
    location: GeoJSONPoint
    observed_at: datetime
    created_at: datetime

    model_config = {"populate_by_name": True}


def doc_to_observation(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    doc["provider_id"] = str(doc["provider_id"])
    return doc
