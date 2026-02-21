from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query

from app.db import get_db
from app.models.observation import (
    ObservationCreate,
    ObservationResponse,
    doc_to_observation,
)

router = APIRouter(prefix="/api/observations", tags=["observations"])


@router.post("", response_model=ObservationResponse, status_code=201)
async def create_observation(body: ObservationCreate):
    db = get_db()

    try:
        provider_oid = ObjectId(body.provider_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid provider_id")

    provider = await db.providers.find_one({"_id": provider_oid})
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    stype = await db.service_types.find_one({"slug": body.service_type})
    if not stype:
        raise HTTPException(status_code=404, detail=f"Service type '{body.service_type}' not found")

    doc = {
        "provider_id": provider_oid,
        "service_type": stype["slug"],
        "category": stype["category"],
        "price": body.price,
        "currency": body.currency,
        "source_type": body.source_type,
        "location": provider["location"],
        "observed_at": body.observed_at or datetime.now(timezone.utc),
        "created_at": datetime.now(timezone.utc),
    }

    result = await db.observations.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc_to_observation(doc)


@router.get("", response_model=list[ObservationResponse])
async def query_observations(
    category: str = Query(..., description="e.g. mechanic, electrician"),
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    radius_meters: float = Query(..., gt=0, description="Search radius in meters"),
    service_type: Optional[str] = Query(default=None, description="Filter by service type slug"),
):
    db = get_db()

    query: dict = {
        "category": category,
        "location": {
            "$nearSphere": {
                "$geometry": {"type": "Point", "coordinates": [lng, lat]},
                "$maxDistance": radius_meters,
            }
        },
    }
    if service_type:
        query["service_type"] = service_type

    cursor = db.observations.find(query)
    docs = await cursor.to_list(length=1000)
    return [doc_to_observation(d) for d in docs]
