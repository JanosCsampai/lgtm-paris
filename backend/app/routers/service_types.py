import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.db import get_db
from app.models.service_type import (
    ServiceTypeCreate,
    ServiceTypeResponse,
    doc_to_service_type,
    service_type_to_doc,
)
from app.services import embeddings as embeddings_svc

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/service-types", tags=["service-types"])


@router.post("", response_model=ServiceTypeResponse, status_code=201)
async def create_service_type(body: ServiceTypeCreate):
    db = get_db()
    doc = service_type_to_doc(body)

    existing = await db.service_types.find_one({"slug": doc["slug"]})
    if existing:
        raise HTTPException(status_code=409, detail=f"Service type '{doc['slug']}' already exists")

    if embeddings_svc.is_available():
        try:
            text = embeddings_svc.build_search_text(
                body.name, body.category, body.description
            )
            vectors = await asyncio.to_thread(
                embeddings_svc.get_embeddings().embed_documents, [text]
            )
            doc["embedding"] = vectors[0]
        except Exception:
            logger.warning("Failed to generate embedding for %s", body.slug, exc_info=True)

    result = await db.service_types.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc_to_service_type(doc)


@router.get("", response_model=list[ServiceTypeResponse])
async def list_service_types(category: Optional[str] = Query(default=None)):
    db = get_db()
    query = {}
    if category:
        query["category"] = category
    cursor = db.service_types.find(query)
    docs = await cursor.to_list(length=500)
    return [doc_to_service_type(d) for d in docs]
