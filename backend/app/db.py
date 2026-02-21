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
    client = AsyncIOMotorClient(settings.mongo_url)
    sync_client = MongoClient(settings.mongo_url)


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
