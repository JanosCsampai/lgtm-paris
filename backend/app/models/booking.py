from datetime import datetime

from pydantic import BaseModel, Field


class BookingCreate(BaseModel):
    customer_id: str = Field(..., description="MongoDB _id of the customer record")
    service_type: str = Field(..., examples=["tire_change"])
    provider_id: str = Field(..., description="MongoDB _id of the provider")
    amount: float = Field(..., gt=0, description="Service price")
    currency: str = Field(default="GBP", examples=["GBP", "EUR"])
    agent_name: str = Field(default="LGTM Agent")


class BookingResponse(BaseModel):
    id: str = Field(..., alias="_id")
    customer_id: str
    service_type: str
    provider_id: str
    amount: float
    currency: str
    status: str
    stripe_payment_intent_id: str
    stripe_cardholder_id: str
    stripe_card_id: str
    card_last4: str
    card_exp_month: int
    card_exp_year: int
    created_at: datetime

    model_config = {"populate_by_name": True}


class BookingWithCardResponse(BookingResponse):
    """Returned only at booking creation — includes the full card details for the AI agent."""
    card_number: str
    card_cvc: str


def doc_to_booking(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc
