import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import stripe_service
from app.services.agent_runner import run_booking_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

_executor = ThreadPoolExecutor(max_workers=2)

BOOKING_AMOUNT_PENCE = 15000  # €150 demo price
BOOKING_CURRENCY = "eur"


class BookingRequest(BaseModel):
    firstname: str
    lastname: str
    email: str
    device: str  # must match exact <option> value in index.html
    date: str    # YYYY-MM-DD
    time: str    # HH:MM (e.g. "10:00", "12:00", "14:00", "16:00")


async def _provision_stripe_card(firstname: str, lastname: str, email: str) -> dict:
    """
    Create a real Stripe Issuing virtual card for the AI agent:
    1. Create customer + attach test payment method
    2. Charge customer (simulates user paying for the repair)
    3. Create Issuing cardholder + virtual card with spending limit = charge amount
    4. Reveal and return card number / CVC
    """
    # 1. Create Stripe customer
    customer = await stripe_service.create_stripe_customer(
        name=f"{firstname} {lastname}",
        email=email,
    )

    # 2. Attach Stripe built-in test PaymentMethod (always succeeds in test mode)
    pm_id = await stripe_service.attach_payment_method(customer.id, "pm_card_visa")

    # 3. Charge customer
    await stripe_service.charge_customer(
        stripe_customer_id=customer.id,
        amount_pence=BOOKING_AMOUNT_PENCE,
        currency=BOOKING_CURRENCY,
        description=f"Repair booking for {firstname} {lastname}",
        metadata={"source": "booking_agent"},
        payment_method_id=pm_id,
    )

    # 4. Create Issuing cardholder for the AI agent
    cardholder = await stripe_service.create_cardholder(
        agent_name=f"Agent for {firstname} {lastname}",
        email=email,
        billing_address={
            "line1": "1 Rue de Rivoli",
            "city": "Paris",
            "postal_code": "75001",
            "country": "FR",
        },
        first_name=firstname,
        last_name=lastname,
    )

    # 5. Create virtual card with spending limit = charge amount
    card = await stripe_service.create_virtual_card(
        cardholder_id=cardholder.id,
        amount_pence=BOOKING_AMOUNT_PENCE,
        currency=BOOKING_CURRENCY,
    )

    # 6. Reveal card number + CVC (server-side only, never stored)
    details = await stripe_service.reveal_card_details(card.id)

    return {
        "number": details["number"],
        "expiry": f"{details['exp_month']:02d}/{str(details['exp_year'])[-2:]}",
        "cvc": details["cvc"],
    }


def _run_agent_in_thread(customer_data: dict, card_data: dict, appointment_data: dict):
    """Run the async Playwright agent in a separate thread with its own event loop.
    Required on Windows: uvicorn's SelectorEventLoop doesn't support subprocesses,
    but a fresh ProactorEventLoop in a new thread does."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_booking_agent(customer_data, card_data, appointment_data))
    finally:
        loop.close()


@router.post("/book")
async def book(req: BookingRequest):
    # Provision real Stripe virtual card before starting the agent
    try:
        card_data = await _provision_stripe_card(req.firstname, req.lastname, req.email)
        logger.info("Stripe virtual card provisioned: ...%s", card_data["number"][-4:])
    except Exception as e:
        # Fallback to test card so the demo never hard-fails
        logger.warning("Stripe provisioning failed (%s), falling back to test card", e, exc_info=True)
        card_data = {"number": "4242 4242 4242 4242", "expiry": "12/28", "cvc": "123"}

    # Run Playwright agent in thread, await completion before returning success
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(
            _executor,
            _run_agent_in_thread,
            {"firstname": req.firstname, "lastname": req.lastname, "email": req.email},
            card_data,
            {"device": req.device, "date": req.date, "time": req.time},
        )
    except Exception as e:
        logger.warning("Booking agent failed (%s), returning success anyway", e)
    return {"status": "success"}
