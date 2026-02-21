# Backend Functionality

> **Plumline — Local Service Price Intelligence** v0.2.0

## Architecture

- **Framework:** FastAPI (async)
- **Database:** MongoDB via Motor (async driver) + pymongo (sync, for LangChain)
- **Search:** Atlas Search (full-text) + Atlas Vector Search (semantic) via LangChain
- **Embeddings:** OpenAI `text-embedding-3-small` via `langchain-openai`
- **Validation:** Pydantic v2
- **Config:** pydantic-settings with `.env` file support

## Data Models

### ServiceType

Defines a type of service offered (e.g. "Tire Change").

| Field         | Type           | Notes                                   |
|---------------|----------------|-----------------------------------------|
| `id`          | `str`          | MongoDB ObjectId                        |
| `slug`        | `str`          | Unique key, e.g. `tire_change`          |
| `name`        | `str`          | Human-readable name                     |
| `category`    | `str`          | e.g. `mechanic`, `electrician`          |
| `description` | `str?`         | Optional description (improves search)  |
| `embedding`   | `list[float]`  | 1536-dim vector (excluded from API responses) |
| `created_at`  | `datetime`     | Auto-set on creation                    |

### Provider

A local service provider with a physical location.

| Field        | Type           | Notes                          |
|--------------|----------------|--------------------------------|
| `id`         | `str`          | MongoDB ObjectId               |
| `name`       | `str`          | Business name                  |
| `category`   | `str`          | e.g. `mechanic`, `electrician` |
| `location`   | `GeoJSONPoint` | `[longitude, latitude]`        |
| `address`    | `str`          | Street address                 |
| `city`       | `str`          | Defaults to `"London"`         |
| `created_at` | `datetime`     | Auto-set on creation           |

### Observation

A single price data point linking a provider to a service type.

| Field          | Type           | Notes                                        |
|----------------|----------------|----------------------------------------------|
| `id`           | `str`          | MongoDB ObjectId                             |
| `provider_id`  | `str`          | References a Provider                        |
| `service_type` | `str`          | Service type slug                            |
| `category`     | `str`          | Inherited from the service type              |
| `price`        | `float`        | Must be > 0                                  |
| `currency`     | `str`          | Defaults to `"EUR"`                          |
| `source_type`  | `str`          | One of: `scrape`, `manual`, `receipt`, `quote` |
| `location`     | `GeoJSONPoint` | Inherited from the provider                  |
| `observed_at`  | `datetime`     | When the price was observed (defaults to now) |
| `created_at`   | `datetime`     | Auto-set on creation                         |

## API Endpoints

### Health

| Method | Path      | Description  |
|--------|-----------|--------------|
| GET    | `/health` | Health check |

### Search — `/api/search`

| Method | Path          | Description |
|--------|---------------|-------------|
| GET    | `/api/search` | Combined text + vector + geo search. Required: `q`, `lat`, `lng`. Optional: `radius_meters` (default 5000). Returns matching service types, nearby providers with price observations, and a `discovery_triggered` flag. |

**Response shape:**

```json
{
  "query": "oil change",
  "matched_service_types": [
    { "slug": "oil_change", "name": "Oil Change", "match_source": "text", "score": 4.2 }
  ],
  "results": [
    {
      "id": "...",
      "name": "QuickFix Garage",
      "category": "mechanic",
      "address": "14 Old Kent Rd",
      "city": "London",
      "location": { "type": "Point", "coordinates": [-0.08, 51.49] },
      "distance_meters": 1200.5,
      "observations": [
        { "service_type": "oil_change", "price": 45.50, "currency": "GBP", "source_type": "manual", "observed_at": "..." }
      ]
    }
  ],
  "discovery_triggered": false
}
```

**Search flow:**

1. Runs Atlas Search (full-text, fuzzy) and Atlas Vector Search (semantic) on `service_types` in parallel.
2. Merges and deduplicates matched service types.
3. Runs a `$geoNear` aggregation on `observations` for the matched service type slugs within the given radius, with a `$lookup` to `providers`, grouped by provider.
4. If no results are found, triggers the external discovery stub (Google Places + Linkup — not yet implemented).

### Service Types — `/api/service-types`

| Method | Path                 | Description                                  |
|--------|----------------------|----------------------------------------------|
| POST   | `/api/service-types` | Create a service type. 409 if slug exists.   |
| GET    | `/api/service-types` | List all (up to 500). Optional `?category=`. |

### Providers — `/api/providers`

| Method | Path                       | Description                                    |
|--------|----------------------------|------------------------------------------------|
| POST   | `/api/providers`           | Create a provider.                             |
| GET    | `/api/providers`           | List all (up to 500). Optional `?category=`.   |
| GET    | `/api/providers/{id}`      | Get a single provider by ID. 404 if not found. |

### Observations — `/api/observations`

| Method | Path                 | Description                                                        |
|--------|----------------------|--------------------------------------------------------------------|
| POST   | `/api/observations`  | Create an observation. Validates provider and service type exist.   |
| GET    | `/api/observations`  | Geospatial query. Required: `category`, `lat`, `lng`, `radius_meters`. Optional: `service_type`. Returns up to 1000 results sorted by distance. |

## Database Indexes

### Standard Indexes

| Collection      | Index                          | Type       |
|-----------------|--------------------------------|------------|
| `service_types` | `slug`                         | Unique     |
| `providers`     | `location`                     | 2dsphere   |
| `observations`  | `location`                     | 2dsphere   |
| `observations`  | `category` + `service_type`    | Compound   |

### Atlas Search Indexes

Created via `python -m scripts.create_search_indexes`.

| Collection      | Index Name              | Type          | Fields / Config                                  |
|-----------------|-------------------------|---------------|--------------------------------------------------|
| `service_types` | `service_types_text`    | Atlas Search  | `name`, `slug`, `category` (luceneStandard)      |
| `service_types` | `service_types_vector`  | Vector Search | `embedding` — 1536 dims, cosine similarity       |

## Services

| Module                        | Purpose                                                    |
|-------------------------------|------------------------------------------------------------|
| `app/services/embeddings.py`  | OpenAI embedding generation via `langchain-openai`         |
| `app/services/search.py`     | Search orchestration (text + vector + geo)                 |
| `app/services/discovery.py`  | External discovery stub (Google Places + Linkup scraping)  |

## Scripts

Run from the `backend/` directory.

### Seed demo data

```bash
python -m scripts.seed
```

Populates demo data for London with:

- **11 service types** across two categories (mechanic, electrician)
- **20 providers** spread across London
- **~100 observations** with randomized prices and dates (last 90 days)

### Create Atlas Search indexes

```bash
python -m scripts.create_search_indexes
```

Creates the `service_types_text` (Atlas Search) and `service_types_vector` (Vector Search) indexes. Idempotent — skips existing indexes.

### Generate embeddings

```bash
python -m scripts.embed_service_types
```

Generates OpenAI embeddings for all service types that don't have one yet. Requires `OPENAI_API_KEY`.

### Seeded Service Types

| Category      | Services                                                                                |
|---------------|-----------------------------------------------------------------------------------------|
| Mechanic      | Oil Change, Tire Change, Brake Pad Replacement, Full Service, MOT Test, Battery Replacement |
| Electrician   | Rewiring, Fuse Box Replacement, Socket Installation, Lighting Installation, EV Charger Install |

## Environment Variables

| Variable        | Default                         | Description                 |
|-----------------|---------------------------------|-----------------------------|
| `MONGO_URL`     | `mongodb://localhost:27017`     | MongoDB connection string   |
| `MONGO_DB`      | `plumline`                    | Database name               |
| `OPENAI_API_KEY`| —                               | Required for search & embeddings |

## Dependencies

| Package            | Purpose                              |
|--------------------|--------------------------------------|
| `fastapi`          | Web framework                        |
| `uvicorn[standard]`| ASGI server                          |
| `motor`            | Async MongoDB driver                 |
| `pydantic[email]`  | Data validation                      |
| `pydantic-settings` | Settings from env                   |
| `python-dotenv`    | `.env` file loading                  |
| `langchain-openai` | OpenAI embeddings via LangChain      |
| `langchain-mongodb`| Atlas Vector Search via LangChain    |

## Notes

- CORS is fully open (all origins, methods, headers).
- No authentication on any endpoint.
- The search endpoint requires Atlas Search indexes to be created first (`python -m scripts.create_search_indexes`) and embeddings to be generated (`python -m scripts.embed_service_types`).
- The external discovery stub in `app/services/discovery.py` logs when triggered but takes no action — it is the integration point for Google Places API and Linkup price scraping.
- Auto-generated API docs available at `/docs` (Swagger UI) and `/redoc`.
