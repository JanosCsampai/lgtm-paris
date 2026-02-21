"""
Generate and store embeddings for all service types that don't have one yet.

Usage (from backend/):
    python -m scripts.embed_service_types

Requires OPENAI_API_KEY to be set in .env.
"""

from pymongo import MongoClient

from app.config import settings
from app.services.embeddings import build_search_text, get_embeddings


def embed_service_types():
    client = MongoClient(settings.mongo_url)
    db = client[settings.mongo_db]
    collection = db.service_types

    docs = list(collection.find({"embedding": {"$exists": False}}))
    if not docs:
        print("All service types already have embeddings — nothing to do.")
        client.close()
        return

    print(f"Generating embeddings for {len(docs)} service types...")

    texts = [
        build_search_text(d["name"], d["category"], d.get("description"))
        for d in docs
    ]

    embeddings_model = get_embeddings()
    vectors = embeddings_model.embed_documents(texts)

    for doc, vector in zip(docs, vectors):
        collection.update_one(
            {"_id": doc["_id"]},
            {"$set": {"embedding": vector}},
        )
        print(f"  ✓ {doc['slug']}")

    print(f"Done — {len(docs)} embeddings stored.")
    client.close()


if __name__ == "__main__":
    embed_service_types()
