"""
Seed script — populates London demo data for mechanics and electricians.

Usage (from backend/):
    python -m scripts.seed

Idempotent: drops and recreates all data on each run.
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

random.seed(42)

SERVICE_TYPES = [
    {"slug": "oil_change", "name": "Oil Change", "category": "mechanic"},
    {"slug": "tire_change", "name": "Tire Change", "category": "mechanic"},
    {"slug": "brake_pad_replacement", "name": "Brake Pad Replacement", "category": "mechanic"},
    {"slug": "full_service", "name": "Full Service", "category": "mechanic"},
    {"slug": "mot_test", "name": "MOT Test", "category": "mechanic"},
    {"slug": "battery_replacement", "name": "Battery Replacement", "category": "mechanic"},
    {"slug": "rewiring", "name": "Full Rewiring", "category": "electrician"},
    {"slug": "fuse_box_replacement", "name": "Fuse Box Replacement", "category": "electrician"},
    {"slug": "socket_installation", "name": "Socket Installation", "category": "electrician"},
    {"slug": "lighting_installation", "name": "Lighting Installation", "category": "electrician"},
    {"slug": "ev_charger_install", "name": "EV Charger Installation", "category": "electrician"},
]

PRICE_RANGES = {
    "oil_change": (35, 120),
    "tire_change": (40, 150),
    "brake_pad_replacement": (80, 300),
    "full_service": (150, 450),
    "mot_test": (35, 55),
    "battery_replacement": (60, 200),
    "rewiring": (2000, 6000),
    "fuse_box_replacement": (300, 800),
    "socket_installation": (50, 150),
    "lighting_installation": (80, 250),
    "ev_charger_install": (600, 1500),
}

PROVIDERS = [
    # Mechanics spread across London
    {"name": "QuickFix Garage", "category": "mechanic", "address": "14 Old Kent Rd, London SE1 5UG", "lng": -0.0825, "lat": 51.4937},
    {"name": "Bermondsey Motors", "category": "mechanic", "address": "87 Bermondsey St, London SE1 3XF", "lng": -0.0818, "lat": 51.4998},
    {"name": "Camden Car Care", "category": "mechanic", "address": "22 Chalk Farm Rd, London NW1 8AG", "lng": -0.1530, "lat": 51.5432},
    {"name": "Hackney Auto Services", "category": "mechanic", "address": "55 Mare St, London E8 4RG", "lng": -0.0556, "lat": 51.5470},
    {"name": "Greenwich Garage", "category": "mechanic", "address": "100 Trafalgar Rd, London SE10 9UX", "lng": -0.0014, "lat": 51.4828},
    {"name": "Brixton Vehicle Centre", "category": "mechanic", "address": "45 Brixton Rd, London SW9 6DE", "lng": -0.1145, "lat": 51.4627},
    {"name": "Islington Autofix", "category": "mechanic", "address": "33 Upper St, London N1 0PN", "lng": -0.1029, "lat": 51.5362},
    {"name": "Lewisham Motor Works", "category": "mechanic", "address": "70 Lewisham High St, London SE13 5JH", "lng": -0.0139, "lat": 51.4545},
    {"name": "Fulham Tyre & Service", "category": "mechanic", "address": "19 Fulham Rd, London SW6 1AH", "lng": -0.1953, "lat": 51.4801},
    {"name": "Stratford Pit Stop", "category": "mechanic", "address": "8 The Grove, London E15 1EL", "lng": -0.0027, "lat": 51.5416},
    # Electricians spread across London
    {"name": "Spark London Electrical", "category": "electrician", "address": "12 Baker St, London W1U 3BU", "lng": -0.1566, "lat": 51.5226},
    {"name": "Southwark Sparks", "category": "electrician", "address": "60 Borough High St, London SE1 1XF", "lng": -0.0907, "lat": 51.5033},
    {"name": "Walthamstow Electrical Co", "category": "electrician", "address": "44 Hoe St, London E17 4PG", "lng": -0.0232, "lat": 51.5830},
    {"name": "Battersea Power Electric", "category": "electrician", "address": "21 Lavender Hill, London SW11 5QW", "lng": -0.1680, "lat": 51.4625},
    {"name": "Shoreditch Circuits", "category": "electrician", "address": "5 Shoreditch High St, London E1 6JE", "lng": -0.0766, "lat": 51.5235},
    {"name": "Croydon Electrics", "category": "electrician", "address": "90 High St, Croydon CR0 1NA", "lng": -0.0987, "lat": 51.3762},
    {"name": "Ealing Electrical Services", "category": "electrician", "address": "38 Broadway, London W5 2HP", "lng": -0.3047, "lat": 51.5093},
    {"name": "Wimbledon Wire Works", "category": "electrician", "address": "15 The Broadway, London SW19 1PS", "lng": -0.2064, "lat": 51.4214},
    {"name": "Kilburn Electrics", "category": "electrician", "address": "72 Kilburn High Rd, London NW6 4HJ", "lng": -0.1917, "lat": 51.5371},
    {"name": "Tower Hamlets Electrical", "category": "electrician", "address": "28 Commercial Rd, London E1 1LR", "lng": -0.0613, "lat": 51.5131},
]

SOURCE_TYPES = ["scrape", "manual", "receipt", "quote"]


async def seed():
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.mongo_db]

    print("Dropping existing collections...")
    await db.service_types.drop()
    await db.providers.drop()
    await db.observations.drop()

    now = datetime.now(timezone.utc)

    print(f"Inserting {len(SERVICE_TYPES)} service types...")
    for st in SERVICE_TYPES:
        st["created_at"] = now
    await db.service_types.insert_many(SERVICE_TYPES)

    print(f"Inserting {len(PROVIDERS)} providers...")
    provider_docs = []
    for p in PROVIDERS:
        provider_docs.append({
            "name": p["name"],
            "category": p["category"],
            "address": p["address"],
            "city": "London",
            "location": {"type": "Point", "coordinates": [p["lng"], p["lat"]]},
            "created_at": now,
        })
    result = await db.providers.insert_many(provider_docs)
    provider_ids = result.inserted_ids

    print("Generating ~100 observations...")
    observations = []
    for _ in range(100):
        idx = random.randint(0, len(provider_docs) - 1)
        provider = provider_docs[idx]
        provider_id = provider_ids[idx]

        category = provider["category"]
        eligible_services = [s for s in SERVICE_TYPES if s["category"] == category]
        service = random.choice(eligible_services)

        low, high = PRICE_RANGES[service["slug"]]
        price = round(random.uniform(low, high), 2)

        days_ago = random.randint(0, 90)
        observed_at = now - timedelta(days=days_ago)

        observations.append({
            "provider_id": provider_id,
            "service_type": service["slug"],
            "category": category,
            "price": price,
            "currency": "GBP",
            "source_type": random.choice(SOURCE_TYPES),
            "location": provider["location"],
            "observed_at": observed_at,
            "created_at": now,
        })

    await db.observations.insert_many(observations)

    from pymongo import GEOSPHERE
    await db.service_types.create_index("slug", unique=True)
    await db.providers.create_index([("location", GEOSPHERE)])
    await db.observations.create_index([("location", GEOSPHERE)])
    await db.observations.create_index([("category", 1), ("service_type", 1)])

    print(f"Done! Seeded {len(SERVICE_TYPES)} service types, {len(PROVIDERS)} providers, {len(observations)} observations.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
