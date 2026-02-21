# Backend Functionality

> **LGTM — Local Service Price Intelligence** v0.1.0

## Architecture

- **Framework:** FastAPI (async)
- **Database:** MongoDB via Motor (async driver)
- **Validation:** Pydantic v2
- **Config:** pydantic-settings with `.env` file support

## Data Models

### ServiceType

Defines a type of service offered (e.g. "Tire Change").

| Field        | Type       | Notes                        |
|--------------|------------|------------------------------|
| `id`         | `str`      | MongoDB ObjectId             |
| `slug`       | `str`      | Unique key, e.g. `tire_change` |
| `name`       | `str`      | Human-readable name          |
| `category`   | `str`      | e.g. `mechanic`, `electrician` |
| `created_at` | `datetime` | Auto-set on creation         |

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

| Collection      | Index                          | Type       |
|-----------------|--------------------------------|------------|
| `service_types` | `slug`                         | Unique     |
| `providers`     | `location`                     | 2dsphere   |
| `observations`  | `location`                     | 2dsphere   |
| `observations`  | `category` + `service_type`    | Compound   |

## Seed Script

Run from the `backend/` directory:

```bash
python -m scripts.seed
```

Populates demo data for London with:

- **11 service types** across two categories (mechanic, electrician)
- **20 providers** spread across London
- **~100 observations** with randomized prices and dates (last 90 days)

### Seeded Service Types

| Category      | Services                                                                                |
|---------------|-----------------------------------------------------------------------------------------|
| Mechanic      | Oil Change, Tire Change, Brake Pad Replacement, Full Service, MOT Test, Battery Replacement |
| Electrician   | Rewiring, Fuse Box Replacement, Socket Installation, Lighting Installation, EV Charger Install |

## Environment Variables

| Variable   | Default                         | Description              |
|------------|---------------------------------|--------------------------|
| `MONGO_URL`| `mongodb://localhost:27017`     | MongoDB connection string |
| `MONGO_DB` | `lgtm`                         | Database name             |

## Dependencies

| Package            | Purpose                     |
|--------------------|-----------------------------|
| `fastapi`          | Web framework               |
| `uvicorn[standard]`| ASGI server                 |
| `motor`            | Async MongoDB driver        |
| `pydantic[email]`  | Data validation             |
| `pydantic-settings` | Settings from env          |
| `python-dotenv`    | `.env` file loading         |

## Notes

- CORS is fully open (all origins, methods, headers).
- No authentication on any endpoint.
- The `app/services/` directory exists but is empty — business logic lives in the routers for now.
- Auto-generated API docs available at `/docs` (Swagger UI) and `/redoc`.
