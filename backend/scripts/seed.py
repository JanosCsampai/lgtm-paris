"""
Seed script — populates London demo data for phone screen repair shops.

Usage (from backend/):
    python -m scripts.seed

Idempotent: drops and recreates all data on each run.
Also generates embeddings if OPENAI_API_KEY is set.
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings

random.seed(42)

SERVICE_TYPES = [
    {"slug": "iphone_screen_repair", "name": "iPhone Screen Repair", "category": "phone_repair", "description": "Cracked or broken iPhone display replacement"},
    {"slug": "samsung_screen_repair", "name": "Samsung Screen Repair", "category": "phone_repair", "description": "Samsung Galaxy cracked screen replacement"},
    {"slug": "ipad_screen_repair", "name": "iPad Screen Repair", "category": "phone_repair", "description": "iPad broken glass or LCD replacement"},
    {"slug": "battery_replacement_phone", "name": "Phone Battery Replacement", "category": "phone_repair", "description": "Worn-out phone battery swap for any brand"},
    {"slug": "back_glass_repair", "name": "Back Glass Repair", "category": "phone_repair", "description": "Rear glass panel replacement for iPhones and Samsung"},
    {"slug": "charging_port_repair", "name": "Charging Port Repair", "category": "phone_repair", "description": "Broken or loose charging port fix"},
    {"slug": "water_damage_repair", "name": "Water Damage Repair", "category": "phone_repair", "description": "Phone water damage diagnostic and repair"},
    {"slug": "camera_repair", "name": "Camera Lens Repair", "category": "phone_repair", "description": "Cracked or blurry phone camera lens replacement"},
    {"slug": "speaker_repair", "name": "Speaker Repair", "category": "phone_repair", "description": "Phone speaker or earpiece replacement"},
    {"slug": "software_fix", "name": "Software Troubleshooting", "category": "phone_repair", "description": "Frozen phone, boot loops, or OS reinstall"},
]

PRICE_RANGES = {
    "iphone_screen_repair": (50, 250),
    "samsung_screen_repair": (45, 220),
    "ipad_screen_repair": (80, 300),
    "battery_replacement_phone": (25, 70),
    "back_glass_repair": (30, 120),
    "charging_port_repair": (30, 90),
    "water_damage_repair": (50, 150),
    "camera_repair": (35, 100),
    "speaker_repair": (25, 80),
    "software_fix": (20, 60),
}

PROVIDERS = [
    {"name": "iSmash Oxford Street", "category": "phone_repair", "address": "274 Oxford St, London W1C 1DS", "lng": -0.1479, "lat": 51.5153, "rating": 4.8, "review_count": 214, "description": "iPhone & Samsung screen replacement in 30 minutes. Original OLED panels, 6-month warranty on all repairs. Walk-ins welcome."},
    {"name": "Repair Lab Shoreditch", "category": "phone_repair", "address": "12 Bethnal Green Rd, London E1 6GY", "lng": -0.0729, "lat": 51.5237, "rating": 4.6, "review_count": 156, "description": "Budget-friendly screen repair for all phone brands. Aftermarket and OEM options available. Same-day service guaranteed."},
    {"name": "Fone World Camden", "category": "phone_repair", "address": "91 Camden High St, London NW1 7JN", "lng": -0.1387, "lat": 51.5392, "rating": 4.3, "review_count": 89, "description": "Walk-in phone repair shop with express 20-minute screen fixes. Free diagnostic on all devices."},
    {"name": "ScreenFix Brixton", "category": "phone_repair", "address": "8 Electric Ave, Brixton, London SW9 8JX", "lng": -0.1142, "lat": 51.4619, "rating": 4.5, "review_count": 132, "description": "Community-trusted repairs since 2016. Specialising in water damage recovery and screen replacements."},
    {"name": "Tech Repair Hub Stratford", "category": "phone_repair", "address": "Unit 3, Westfield Stratford, London E20 1EJ", "lng": -0.0065, "lat": 51.5437, "rating": 4.7, "review_count": 278, "description": "Premium repair centre inside Westfield. Genuine parts for iPhone, Samsung, and Google Pixel. 12-month warranty."},
    {"name": "Phone Surgeon Islington", "category": "phone_repair", "address": "55 Upper St, Islington, London N1 0NY", "lng": -0.1030, "lat": 51.5362, "rating": 4.9, "review_count": 327, "description": "Apple-certified screen repairs for iPhone, iPad, and MacBook. Genuine Apple parts, calibrated True Tone display. 12-month warranty."},
    {"name": "QuickFix Phones Lewisham", "category": "phone_repair", "address": "35 Lewisham High St, London SE13 5AF", "lng": -0.0141, "lat": 51.4543, "rating": 4.4, "review_count": 98, "description": "Affordable repairs with no appointment needed. Screen, battery, and charging port fixes while you wait."},
    {"name": "Mobile Rescue Fulham", "category": "phone_repair", "address": "22 North End Rd, Fulham, London SW6 1NB", "lng": -0.1953, "lat": 51.4834, "rating": 4.2, "review_count": 67, "description": "Local phone repair with pickup and delivery service. Evening and weekend appointments available."},
    {"name": "Cracked It Greenwich", "category": "phone_repair", "address": "15 Greenwich Church St, London SE10 9BJ", "lng": -0.0098, "lat": 51.4789, "rating": 4.6, "review_count": 143, "description": "Expert glass and LCD repairs for all major brands. Student discount available. Open 7 days a week."},
    {"name": "Dr Screen Hackney", "category": "phone_repair", "address": "42 Mare St, Hackney, London E8 4RP", "lng": -0.0556, "lat": 51.5470, "rating": 4.1, "review_count": 54, "description": "Micro-soldering specialists. Complex board-level repairs alongside standard screen and battery swaps."},
    {"name": "PhoneFix Express Covent Garden", "category": "phone_repair", "address": "9 Neal St, London WC2H 9PW", "lng": -0.1266, "lat": 51.5139, "rating": 4.7, "review_count": 201, "description": "Central London express repairs. Most screens replaced in under 25 minutes. Premium and budget part options."},
    {"name": "iRepair Tottenham Court Rd", "category": "phone_repair", "address": "120 Tottenham Court Rd, London W1T 5AA", "lng": -0.1312, "lat": 51.5207, "rating": 4.5, "review_count": 189, "description": "Tech-focused repair shop with transparent pricing. Live repair tracking and lifetime warranty on labour."},
    {"name": "Gadget Fix Bermondsey", "category": "phone_repair", "address": "71 Bermondsey St, London SE1 3XF", "lng": -0.0818, "lat": 51.4998, "rating": 4.3, "review_count": 76, "description": "Multi-device repair hub: phones, tablets, laptops. Same-day turnaround on most screen replacements."},
    {"name": "FixMyPhone Kilburn", "category": "phone_repair", "address": "58 Kilburn High Rd, London NW6 4HJ", "lng": -0.1917, "lat": 51.5371, "rating": 4.0, "review_count": 52, "description": "Neighbourhood repair shop with honest pricing. No fix, no fee policy. Battery and screen repairs from £25."},
    {"name": "SmashTech Croydon", "category": "phone_repair", "address": "22 High St, Croydon CR0 1YA", "lng": -0.0987, "lat": 51.3762, "rating": 4.4, "review_count": 115, "description": "South London's trusted repair service. Mail-in option available for all phone models. Free return shipping."},
    {"name": "WeFix Ealing", "category": "phone_repair", "address": "14 The Broadway, London W5 2NR", "lng": -0.3047, "lat": 51.5093, "rating": 4.6, "review_count": 167, "description": "Family-run repair business. Specialising in iPhone and Samsung screens with OEM-grade parts. Kids' tablet repairs too."},
    {"name": "Screen Saviour Wimbledon", "category": "phone_repair", "address": "5 The Broadway, Wimbledon, London SW19 1PS", "lng": -0.2064, "lat": 51.4214, "rating": 4.8, "review_count": 234, "description": "Rated best phone repair in SW London. Same-day screen and battery replacements. Appointment and walk-in."},
    {"name": "Fone Doctor Walthamstow", "category": "phone_repair", "address": "30 Hoe St, London E17 4PG", "lng": -0.0232, "lat": 51.5830, "rating": 3.9, "review_count": 48, "description": "Budget-friendly phone fixes in East London. Quick turnaround on screens, ports, and batteries."},
    {"name": "CellCare Tower Bridge", "category": "phone_repair", "address": "3 Tooley St, London SE1 2PF", "lng": -0.0757, "lat": 51.5050, "rating": 4.7, "review_count": 198, "description": "Corporate and walk-in phone repair near Tower Bridge. Volume discounts for businesses. All parts in stock."},
    {"name": "ProFix Phones Battersea", "category": "phone_repair", "address": "18 Lavender Hill, London SW11 5RW", "lng": -0.1680, "lat": 51.4625, "rating": 4.5, "review_count": 141, "description": "Professional repairs with a personal touch. Free screen protector with every repair. Open late on Thursdays."},
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

    # --- Generate embeddings if possible ---
    embeddings_available = False
    try:
        from app.services.embeddings import build_search_text, get_embeddings, is_available

        if is_available():
            emb = get_embeddings()
            texts = [
                build_search_text(st["name"], st["category"], st.get("description"))
                for st in SERVICE_TYPES
            ]
            vectors = emb.embed_documents(texts)
            for st, vec in zip(SERVICE_TYPES, vectors):
                st["embedding"] = vec
            embeddings_available = True
            print("Generated embeddings for service types.")
    except Exception as e:
        print(f"Skipping embeddings: {e}")

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
            "rating": p.get("rating"),
            "review_count": p.get("review_count"),
            "description": p.get("description"),
            "created_at": now,
        })
    result = await db.providers.insert_many(provider_docs)
    provider_ids = result.inserted_ids

    print("Generating ~150 observations...")
    observations = []
    for _ in range(150):
        idx = random.randint(0, len(provider_docs) - 1)
        provider = provider_docs[idx]
        provider_id = provider_ids[idx]

        service = random.choice(SERVICE_TYPES)
        low, high = PRICE_RANGES[service["slug"]]
        price = round(random.uniform(low, high), 2)

        days_ago = random.randint(0, 90)
        observed_at = now - timedelta(days=days_ago)

        observations.append({
            "provider_id": provider_id,
            "service_type": service["slug"],
            "category": service["category"],
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

    embed_note = " (with embeddings)" if embeddings_available else " (no embeddings — run embed_service_types)"
    print(f"Done! Seeded {len(SERVICE_TYPES)} service types, {len(PROVIDERS)} providers, {len(observations)} observations{embed_note}.")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed())
