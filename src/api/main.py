from fastapi import FastAPI
from src.core.database import init_db

app = FastAPI(
    title="DeliverInno API",
    description="Delivery service API for sellers and buyers",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "deliverinno"}
