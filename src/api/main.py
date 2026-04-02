from fastapi import FastAPI
from src.core.database import init_db
from src.api.routers.buyer import router as buyer_router
from src.api.routers.auth import router as auth_router


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


app.include_router(buyer_router)
app.include_router(auth_router)
