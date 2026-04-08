from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.core.database import init_db
from src.api.routers.buyer import router as buyer_router
from src.api.routers.auth import router as auth_router
from src.api.routers.seller import router as seller_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="DeliverInno API",
    description="Delivery service API for sellers and buyers",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "deliverinno"}

app.include_router(buyer_router)
app.include_router(auth_router)
app.include_router(seller_router)
