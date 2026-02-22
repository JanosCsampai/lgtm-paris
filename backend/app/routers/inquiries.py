import logging

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from app.db import get_db
from app.models.inquiry import InquiryCreate, InquiryResponse, doc_to_inquiry
from app.services.email_service import check_for_replies, is_email_configured, send_inquiry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/inquiries", tags=["inquiries"])


@router.post("", response_model=InquiryResponse, status_code=201)
async def create_inquiry(body: InquiryCreate):
    if not is_email_configured():
        raise HTTPException(
            status_code=503,
            detail="Email sending is not configured. Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, and FROM_EMAIL.",
        )

    try:
        ObjectId(body.provider_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid provider_id")

    try:
        doc = await send_inquiry(body.provider_id, body.service_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to send inquiry")
        raise HTTPException(status_code=500, detail="Failed to send inquiry email")

    return doc


@router.post("/check-replies")
async def check_replies():
    """Manually trigger a check for email replies."""
    count = await check_for_replies()
    return {"replies_processed": count}


@router.get("/{provider_id}")
async def get_provider_inquiries(provider_id: str):
    try:
        oid = ObjectId(provider_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid provider_id")

    db = get_db()
    docs = []
    async for doc in db.inquiries.find({"provider_id": oid}).sort("created_at", -1):
        docs.append(doc_to_inquiry(doc))
    return docs
