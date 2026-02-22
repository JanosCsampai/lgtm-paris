import asyncio

import stripe

from app.config import settings

stripe.api_key = settings.stripe_secret_key


async def create_stripe_customer(name: str, email: str) -> stripe.Customer:
    return await asyncio.to_thread(
        stripe.Customer.create,
        name=name,
        email=email,
        metadata={"source": "plumline"},
    )


async def create_setup_intent(stripe_customer_id: str) -> stripe.SetupIntent:
    return await asyncio.to_thread(
        stripe.SetupIntent.create,
        customer=stripe_customer_id,
        payment_method_types=["card"],
    )


async def attach_payment_method(
    stripe_customer_id: str,
    payment_method_id: str,
) -> str:
    pm = await asyncio.to_thread(
        stripe.PaymentMethod.attach,
        payment_method_id,
        customer=stripe_customer_id,
    )
    await asyncio.to_thread(
        stripe.Customer.modify,
        stripe_customer_id,
        invoice_settings={"default_payment_method": pm.id},
    )
    return pm.id


async def charge_customer(
    stripe_customer_id: str,
    amount_pence: int,
    currency: str,
    description: str,
    metadata: dict,
    payment_method_id: str | None = None,
) -> stripe.PaymentIntent:
    kwargs: dict = dict(
        amount=amount_pence,
        currency=currency,
        customer=stripe_customer_id,
        confirm=True,
        off_session=True,
        description=description,
        metadata=metadata,
    )
    if payment_method_id:
        kwargs["payment_method"] = payment_method_id
    return await asyncio.to_thread(stripe.PaymentIntent.create, **kwargs)


async def topup_platform_balance(amount_pence: int, currency: str) -> stripe.Topup:
    """Fund the platform test balance so Issuing cards can be authorized. Test mode only."""
    return await asyncio.to_thread(
        stripe.Topup.create,
        amount=amount_pence,
        currency=currency,
        description="Plumline platform top-up for issuing",
        statement_descriptor="Plumline",
    )


async def create_cardholder(
    agent_name: str,
    email: str,
    billing_address: dict,
    first_name: str = "Demo",
    last_name: str = "Agent",
) -> stripe.issuing.Cardholder:
    return await asyncio.to_thread(
        stripe.issuing.Cardholder.create,
        name=agent_name,
        email=email,
        type="individual",
        billing={"address": billing_address},
        phone_number="+33600000000",
        status="active",
        individual={
            "first_name": first_name,
            "last_name": last_name,
            "dob": {"day": 1, "month": 1, "year": 1990},
        },
    )


async def create_virtual_card(
    cardholder_id: str,
    amount_pence: int,
    currency: str,
) -> stripe.issuing.Card:
    return await asyncio.to_thread(
        stripe.issuing.Card.create,
        cardholder=cardholder_id,
        type="virtual",
        currency=currency,
        status="active",
        spending_controls={
            "spending_limits": [
                {
                    "amount": amount_pence,
                    "interval": "all_time",
                }
            ],
        },
    )


async def reveal_card_details(card_id: str) -> dict:
    """Retrieve full card details including PAN and CVC. Works server-side in test mode."""
    card = await asyncio.to_thread(
        stripe.issuing.Card.retrieve,
        card_id,
        expand=["number", "cvc"],
    )
    return {
        "number": card.number,
        "cvc": card.cvc,
        "exp_month": card.exp_month,
        "exp_year": card.exp_year,
        "last4": card.last4,
    }
