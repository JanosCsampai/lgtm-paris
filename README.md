# LGTM — Local Service Price Intelligence

Price transparency for local services. Compare what mechanics, electricians, and other service providers charge in your area.

## Quickstart

**Prerequisites:** Python 3.11+

### 1. Clone & configure

```bash
git clone <repo-url> && cd lgtm-paris
cp .env.example .env
```

Edit `.env` and paste the shared MongoDB Atlas connection string:

```
MONGO_URL=mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
MONGO_DB=lgtm
```

### 2. Install & run the backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Seed demo data (20 London providers, ~100 price observations):

```bash
python -m scripts.seed
```

Start the API:

```bash
uvicorn app.main:app --reload
```

API is live at **http://localhost:8000** — Swagger docs at **http://localhost:8000/docs**

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/service-types` | Create a service type |
| GET | `/api/service-types` | List service types (`?category=mechanic`) |
| POST | `/api/providers` | Create a provider |
| GET | `/api/providers` | List providers (`?category=electrician`) |
| GET | `/api/providers/{id}` | Get a single provider |
| POST | `/api/observations` | Create a price observation |
| GET | `/api/observations` | Geo query (`?category=mechanic&lat=51.50&lng=-0.12&radius_meters=5000`) |

## Project Structure

```
lgtm-paris/
├── backend/          # FastAPI + MongoDB (Motor)
│   ├── app/          # Application code
│   ├── scripts/      # Seed script
│   └── requirements.txt
├── frontend/         # Next.js (coming soon)
└── README.md
```