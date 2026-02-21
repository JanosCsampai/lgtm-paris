from datetime import datetime

from pydantic import BaseModel, Field


class StripeCustomerCreate(BaseModel):
    name: str = Field(..., examples=["Alice Martin"])
    email: str = Field(..., examples=["alice@example.com"])


class StripeCustomerResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    email: str
    stripe_customer_id: str
    created_at: datetime

    model_config = {"populate_by_name": True}


def doc_to_stripe_customer(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc
