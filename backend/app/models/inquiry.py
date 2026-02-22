from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class InquiryCreate(BaseModel):
    provider_id: str = Field(..., description="ObjectId of the provider")
    service_type: str = Field(..., description="Slug of the service type")


class InquiryResponse(BaseModel):
    id: str = Field(..., alias="_id")
    provider_id: str
    provider_name: str
    service_type: str
    email_to: str
    subject: str
    body: str
    message_id: str
    status: Literal["sent", "replied", "bounced", "failed"]
    reply_body: Optional[str] = None
    extracted_price: Optional[float] = None
    extracted_currency: Optional[str] = None
    sent_at: datetime
    replied_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"populate_by_name": True}


def doc_to_inquiry(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    doc["provider_id"] = str(doc["provider_id"])
    return doc
