from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.db import get_db
from app.models.booking import (
    BookingCreate,
    BookingWithCardResponse,
    doc_to_booking,
)
from app.models.stripe_customer import (
    StripeCustomerCreate,
    StripeCustomerResponse,
    doc_to_stripe_customer,
)
from app.services import stripe_service

router = APIRouter(prefix="/api/stripe", tags=["stripe"])


# ── Customers ──────────────────────────────────────────────────────────────


@router.post("/customers", response_model=StripeCustomerResponse, status_code=201)
async def create_customer(body: StripeCustomerCreate):
    """Register a customer in Stripe and store them in MongoDB."""
    db = get_db()
    stripe_customer = await stripe_service.create_stripe_customer(body.name, body.email)

    doc = {
        "name": body.name,
        "email": body.email,
        "stripe_customer_id": stripe_customer.id,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.stripe_customers.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc_to_stripe_customer(doc)


@router.post("/customers/{customer_id}/setup-intent")
async def create_setup_intent(customer_id: str):
    """
    Create a SetupIntent to save a payment method for future use.
    For the demo: use test payment method IDs (e.g. pm_card_visa) via attach-payment-method instead.
    """
    db = get_db()
    customer = await db.stripe_customers.find_one({"_id": ObjectId(customer_id)})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    intent = await stripe_service.create_setup_intent(customer["stripe_customer_id"])
    return {"client_secret": intent.client_secret, "setup_intent_id": intent.id}


@router.post("/customers/{customer_id}/attach-payment-method")
async def attach_payment_method(customer_id: str, payment_method_id: str):
    """
    Attach a PaymentMethod to the customer and set it as default.
    In test mode use pm_card_visa (Visa 4242, always succeeds) or pm_card_mastercard.
    """
    db = get_db()
    customer = await db.stripe_customers.find_one({"_id": ObjectId(customer_id)})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    await stripe_service.attach_payment_method(
        customer["stripe_customer_id"], payment_method_id
    )
    return {"status": "attached", "payment_method_id": payment_method_id}


# ── Bookings (main flow) ───────────────────────────────────────────────────


@router.post("/bookings", response_model=BookingWithCardResponse, status_code=201)
async def create_booking(body: BookingCreate):
    """
    Full booking flow:
    1. Validate customer and provider
    2. Charge customer's saved payment method
    3. Top-up platform test balance (required for Stripe Issuing in test mode)
    4. Create Issuing Cardholder for the AI agent
    5. Create virtual card with spending limit = charge amount
    6. Reveal card number + CVC
    7. Persist booking in MongoDB (PAN/CVC never stored)
    8. Return full card details for the AI agent to use at the provider's website
    """
    db = get_db()

    customer = await db.stripe_customers.find_one({"_id": ObjectId(body.customer_id)})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    provider = await db.providers.find_one({"_id": ObjectId(body.provider_id)})
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    amount_pence = int(round(body.amount * 100))
    currency = body.currency.lower()

    payment_intent = await stripe_service.charge_customer(
        stripe_customer_id=customer["stripe_customer_id"],
        amount_pence=amount_pence,
        currency=currency,
        description=f"Plumline booking: {body.service_type} at {provider['name']}",
        metadata={
            "service_type": body.service_type,
            "provider_id": body.provider_id,
        },
    )

    await stripe_service.topup_platform_balance(amount_pence, currency)

    cardholder = await stripe_service.create_cardholder(
        agent_name=body.agent_name,
        email=customer["email"],
        billing_address={
            "line1": provider.get("address", "1 High Street"),
            "city": provider.get("city", "London"),
            "postal_code": "SW1A 1AA",
            "country": "GB",
        },
    )

    card = await stripe_service.create_virtual_card(
        cardholder_id=cardholder.id,
        amount_pence=amount_pence,
        currency=currency,
    )

    card_details = await stripe_service.reveal_card_details(card.id)

    doc = {
        "customer_id": body.customer_id,
        "service_type": body.service_type,
        "provider_id": body.provider_id,
        "amount": body.amount,
        "currency": body.currency,
        "status": "charged",
        "stripe_payment_intent_id": payment_intent.id,
        "stripe_cardholder_id": cardholder.id,
        "stripe_card_id": card.id,
        "card_last4": card_details["last4"],
        "card_exp_month": card_details["exp_month"],
        "card_exp_year": card_details["exp_year"],
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.bookings.insert_one(doc)
    doc["_id"] = result.inserted_id

    response = doc_to_booking(doc)
    response["card_number"] = card_details["number"]
    response["card_cvc"] = card_details["cvc"]
    return response


@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    """Retrieve a booking by ID. Card PAN/CVC are not returned here."""
    db = get_db()
    doc = await db.bookings.find_one({"_id": ObjectId(booking_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Booking not found")
    return doc_to_booking(doc)


# ── Test utility ───────────────────────────────────────────────────────────


@router.post("/topup", status_code=201)
async def topup(amount: float, currency: str = "gbp"):
    """Manually top-up the platform test balance. Useful before running bookings."""
    amount_pence = int(round(amount * 100))
    topup_obj = await stripe_service.topup_platform_balance(amount_pence, currency.lower())
    return {
        "topup_id": topup_obj.id,
        "amount": amount,
        "currency": currency,
        "status": topup_obj.status,
    }
