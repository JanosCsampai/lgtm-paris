from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import db
from app.routers import observations, providers, service_types, stripe_payments, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await db.ensure_indexes()
    yield
    await db.close()


app = FastAPI(
    title="LGTM — Local Service Price Intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(service_types.router)
app.include_router(providers.router)
app.include_router(observations.router)
app.include_router(search.router)
app.include_router(stripe_payments.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
