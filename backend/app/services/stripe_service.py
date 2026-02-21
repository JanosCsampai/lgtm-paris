import asyncio

import stripe

from app.config import settings

stripe.api_key = settings.stripe_secret_key


async def create_stripe_customer(name: str, email: str) -> stripe.Customer:
    return await asyncio.to_thread(
        stripe.Customer.create,
        name=name,
        email=email,
        metadata={"source": "lgtm"},
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
) -> None:
    await asyncio.to_thread(
        stripe.PaymentMethod.attach,
        payment_method_id,
        customer=stripe_customer_id,
    )
    await asyncio.to_thread(
        stripe.Customer.modify,
        stripe_customer_id,
        invoice_settings={"default_payment_method": payment_method_id},
    )


async def charge_customer(
    stripe_customer_id: str,
    amount_pence: int,
    currency: str,
    description: str,
    metadata: dict,
) -> stripe.PaymentIntent:
    return await asyncio.to_thread(
        stripe.PaymentIntent.create,
        amount=amount_pence,
        currency=currency,
        customer=stripe_customer_id,
        payment_method_types=["card"],
        confirm=True,
        off_session=True,
        description=description,
        metadata=metadata,
    )


async def topup_platform_balance(amount_pence: int, currency: str) -> stripe.Topup:
    """Fund the platform test balance so Issuing cards can be authorized. Test mode only."""
    return await asyncio.to_thread(
        stripe.Topup.create,
        amount=amount_pence,
        currency=currency,
        description="LGTM platform top-up for issuing",
        statement_descriptor="LGTM Topup",
    )


async def create_cardholder(
    agent_name: str,
    email: str,
    billing_address: dict,
) -> stripe.issuing.Cardholder:
    return await asyncio.to_thread(
        stripe.issuing.Cardholder.create,
        name=agent_name,
        email=email,
        type="individual",
        billing={"address": billing_address},
        status="active",
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
