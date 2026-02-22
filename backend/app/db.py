import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import GEOSPHERE, MongoClient

from app.config import settings

client: AsyncIOMotorClient = None  # type: ignore[assignment]
sync_client: MongoClient = None  # type: ignore[assignment]


def get_db():
    return client[settings.mongo_db]


def get_sync_db():
    """Synchronous DB handle — used by LangChain integrations that require pymongo."""
    return sync_client[settings.mongo_db]


async def connect():
    global client, sync_client
    client = AsyncIOMotorClient(
        settings.mongo_url,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
        socketTimeoutMS=5000,
    )
    sync_client = MongoClient(
        settings.mongo_url,
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
        socketTimeoutMS=5000,
    )


async def close():
    global client, sync_client
    if client:
        client.close()
    if sync_client:
        sync_client.close()


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

    await db.inquiries.create_index([("provider_id", 1), ("service_type", 1)])
    await db.inquiries.create_index("status")
    await db.inquiries.create_index("message_id", unique=True)
