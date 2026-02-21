"""
Create Atlas Search and Atlas Vector Search indexes on the service_types collection.

Usage (from backend/):
    python -m scripts.create_search_indexes

Requires a MongoDB Atlas cluster (indexes are not available on local mongod).
The script is idempotent — it skips indexes that already exist.
"""

import time

from pymongo import MongoClient
from pymongo.operations import SearchIndexModel

from app.config import settings
from app.services.embeddings import EMBEDDING_DIMENSIONS

TEXT_INDEX_NAME = "service_types_text"
VECTOR_INDEX_NAME = "service_types_vector"


def create_indexes():
    client = MongoClient(settings.mongo_url)
    db = client[settings.mongo_db]
    collection = db.service_types

    existing = {idx["name"] for idx in collection.list_search_indexes()}

    if TEXT_INDEX_NAME in existing:
        print(f"  ✓ Atlas Search index '{TEXT_INDEX_NAME}' already exists — skipping.")
    else:
        print(f"  Creating Atlas Search index '{TEXT_INDEX_NAME}'...")
        text_index = SearchIndexModel(
            definition={
                "mappings": {
                    "dynamic": False,
                    "fields": {
                        "name": {"type": "string", "analyzer": "lucene.standard"},
                        "slug": {"type": "string", "analyzer": "lucene.standard"},
                        "category": {"type": "string", "analyzer": "lucene.standard"},
                    },
                }
            },
            name=TEXT_INDEX_NAME,
            type="search",
        )
        collection.create_search_index(text_index)
        print(f"  ✓ '{TEXT_INDEX_NAME}' created.")

    if VECTOR_INDEX_NAME in existing:
        print(f"  ✓ Vector Search index '{VECTOR_INDEX_NAME}' already exists — skipping.")
    else:
        print(f"  Creating Vector Search index '{VECTOR_INDEX_NAME}'...")
        vector_index = SearchIndexModel(
            definition={
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": EMBEDDING_DIMENSIONS,
                        "similarity": "cosine",
                    }
                ]
            },
            name=VECTOR_INDEX_NAME,
            type="vectorSearch",
        )
        collection.create_search_index(vector_index)
        print(f"  ✓ '{VECTOR_INDEX_NAME}' created.")

    print("\nWaiting for indexes to become ready (this may take a minute on Atlas)...")
    _wait_for_indexes(collection, {TEXT_INDEX_NAME, VECTOR_INDEX_NAME})
    print("Done — all indexes ready.")
    client.close()


def _wait_for_indexes(collection, expected_names: set[str], timeout: int = 120):
    deadline = time.time() + timeout
    while time.time() < deadline:
        ready = set()
        for idx in collection.list_search_indexes():
            if idx["name"] in expected_names and idx.get("status") == "READY":
                ready.add(idx["name"])
        if ready == expected_names:
            return
        time.sleep(5)
    print("  ⚠ Timed out waiting — indexes may still be building on Atlas.")


if __name__ == "__main__":
    create_indexes()
