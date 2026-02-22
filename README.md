# Plumline — Local Service Price Intelligence
### Devpost Project Link: https://devpost.com/software/lgtm-kr23o9
Price transparency for local services. Find out what mechanics, electricians, phone repair shops, and other providers actually charge in your area — powered by multi-layered web scraping, LLM extraction, vector search, and browser automation.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4, shadcn/ui, Radix UI |
| **Maps** | Leaflet + react-leaflet with OpenStreetMap (Carto basemaps) |
| **Backend** | FastAPI (async), Pydantic v2 |
| **Database** | MongoDB Atlas (Motor async driver) |
| **Search** | MongoDB Atlas Search (full-text, fuzzy) + Atlas Vector Search (cosine similarity) |
| **Embeddings** | OpenAI `text-embedding-3-small` (1536 dims) via LangChain |
| **LLM** | GPT-4o-mini — price extraction, email drafting, chat refinement |
| **Scraping** | httpx, BeautifulSoup4, Playwright (async Chromium) |
| **External APIs** | SerpAPI (Google Maps discovery), Linkup SDK (web price search) |
| **Payments** | Stripe Issuing (virtual cards with spending limits) |
| **Email** | SMTP / IMAP (smtplib, imaplib) |
| **Infra** | Docker Compose (MongoDB 7 + FastAPI) |

## Features

### OpenStreetMap with Live Provider Pins

Results are displayed on an interactive Leaflet map backed by OpenStreetMap / Carto tiles. Each provider appears as a pin with its price label. The map auto-fits bounds to all visible results and shows a blue dot for the user's location. On mobile the map stacks below the list; on desktop it's a split view.

### Multi-Tier Price Scraping

Prices are discovered through a three-level cascade — each tier fires only if the previous one comes up empty:

1. **Regex scraping** — A multi-level crawl (homepage, top 3 links, top 2 sub-links) extracts prices with a currency-aware regex (`£`, `€`, `$`). URLs are scored by query-token overlap so the most relevant pages are crawled first. Context-aware matching inspects surrounding HTML containers to avoid false positives.

2. **LLM extraction** — If regex finds nothing and there's enough token overlap (>= 2), the scraped page text is sent to GPT-4o-mini which semantically matches service descriptions (e.g. "chain replacement" ↔ "chain fitting") and returns structured prices.

3. **Linkup web search** — Last resort. The Linkup SDK runs a domain-scoped web search with a circuit-breaker (120 s cooldown after timeout). Source URLs are validated against the provider's domain and the answer is parsed by the LLM.

Scraping happens in the background: the API returns partial results immediately and the frontend polls every 3 s while `scraping_in_progress` is true.

### Vector-Space Price Observation

Service types are embedded with OpenAI `text-embedding-3-small` into a 1536-dimensional vector space. When a user searches, both a full-text Atlas Search query **and** a cosine-similarity Atlas Vector Search query run in parallel. Results are merged and deduplicated (vector score >= 0.75, text score >= 0.10). This makes it easy to find the best price for the most similar service at the closest location — even when wording differs between providers.

### Playwright Auto-Buy

When a user decides to book, the system:

1. Provisions a **Stripe Issuing virtual card** with a spending limit.
2. Launches a headless Chromium browser via **Playwright**.
3. Navigates to the provider's booking page, fills in name, email, device/vehicle, date, time, and card details.
4. Submits the form and waits for confirmation.

The entire flow runs in a background thread with its own event loop so it doesn't block the API.

### Email Automation for Inquiries

For providers without public pricing, the system:

1. **Discovers contact emails** by scraping the provider's homepage, `/contact`, `/about`, and `/impressum` pages (filtering out common platform domains).
2. **Drafts a personalised inquiry** using GPT-4o-mini — professional tone, asks for pricing on the specific service.
3. **Sends it via SMTP** and stores the inquiry with its `Message-ID`.
4. **Monitors the inbox via IMAP** — matches replies by `In-Reply-To` / `References` headers, extracts prices from the reply body with the LLM, and automatically creates price observations.

### Conversational Search Refinement

A chat interface (GPT-4o-mini) guides the user through one question at a time — collecting device/brand/model for repairs, make/model for vehicles, or job details for trade services — then returns a ready-to-search query.

### SerpAPI Provider Discovery

When the local database has no results, the system queries SerpAPI's Google Maps endpoint to discover businesses matching the query within the user's radius. New providers are upserted into MongoDB and embeddings are generated on the fly.

## Running It

```bash
# 1. Clone & configure
git clone <repo-url> && cd lgtm-paris
cp backend/.env.example backend/.env   # fill in MONGO_URL, OPENAI_API_KEY, etc.

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.create_search_indexes   # one-time: Atlas Search + Vector indexes
python -m scripts.seed                    # optional: 20 demo providers, ~100 observations
uvicorn app.main:app --reload             # http://localhost:8000

# 3. Frontend
cd ../frontend
npm install
npm run dev                               # http://localhost:3000
```

Or with Docker:

```bash
docker-compose up   # MongoDB 7 + FastAPI backend
```

### Environment Variables (backend)

| Variable | Required | Purpose |
|----------|----------|---------|
| `MONGO_URL` | Yes | MongoDB Atlas connection string |
| `MONGO_DB` | Yes | Database name |
| `OPENAI_API_KEY` | Yes | Embeddings + LLM extraction |
| `SERPAPI_KEY` | No | Google Maps provider discovery |
| `LINKUP_API_KEY` | No | Linkup web price search |
| `STRIPE_SECRET_KEY` | No | Auto-buy virtual cards |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `IMAP_HOST`, `IMAP_PORT`, `FROM_EMAIL` | No | Email inquiry automation |
