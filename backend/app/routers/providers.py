from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Query

from app.db import get_db
from app.models.provider import (
    ProviderCreate,
    ProviderResponse,
    doc_to_provider,
    provider_to_doc,
)

router = APIRouter(prefix="/api/providers", tags=["providers"])


@router.post("", response_model=ProviderResponse, status_code=201)
async def create_provider(body: ProviderCreate):
    db = get_db()
    doc = provider_to_doc(body)
    result = await db.providers.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc_to_provider(doc)


@router.get("", response_model=list[ProviderResponse])
async def list_providers(category: Optional[str] = Query(default=None)):
    db = get_db()
    query = {}
    if category:
        query["category"] = category
    cursor = db.providers.find(query)
    docs = await cursor.to_list(length=500)
    return [doc_to_provider(d) for d in docs]


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: str):
    db = get_db()
    try:
        oid = ObjectId(provider_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid provider ID")

    doc = await db.providers.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Provider not found")
    return doc_to_provider(doc)
