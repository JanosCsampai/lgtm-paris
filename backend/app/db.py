import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import GEOSPHERE

from app.config import settings

client: AsyncIOMotorClient = None  # type: ignore[assignment]


def get_db():
    return client[settings.mongo_db]


async def connect():
    global client
    client = AsyncIOMotorClient(settings.mongo_url, tlsCAFile=certifi.where())


async def close():
    global client
    if client:
        client.close()


async def ensure_indexes():
    db = get_db()

    await db.service_types.create_index("slug", unique=True)

    await db.providers.create_index([("location", GEOSPHERE)])

    await db.observations.create_index([("location", GEOSPHERE)])
    await db.observations.create_index([("category", 1), ("service_type", 1)])

    await db.stripe_customers.create_index("email", unique=True)
    await db.stripe_customers.create_index("stripe_customer_id", unique=True)

    await db.bookings.create_index("stripe_payment_intent_id", unique=True)
    await db.bookings.create_index("stripe_card_id", unique=True)
    await db.bookings.create_index("customer_id")
