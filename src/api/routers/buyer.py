"""Buyer API endpoints for browsing products, managing cart and orders."""

from typing import List
from sqlite3 import Connection

from fastapi import APIRouter, Depends, status

from src.api.dependencies import get_db_conn, require_buyer
from src.services import buyer_service
from src.shared.models.buyer import (
    ProductResponse,
    CartItemResponse,
    OrderResponse,
    AddToCartRequest,
)

router = APIRouter(prefix="/buyer", tags=["buyer"])


@router.get("/products", response_model=List[ProductResponse])
def list_products(conn: Connection = Depends(get_db_conn)):
    """Get all available products with quantity > 0."""
    return buyer_service.list_products(conn)


@router.post("/cart", status_code=status.HTTP_201_CREATED)
def add_to_cart(
    payload: AddToCartRequest,
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """Add product to buyer's cart and decrease product quantity."""
    return buyer_service.add_to_cart(conn, user["id"], payload)


@router.get("/cart", response_model=List[CartItemResponse])
def get_cart(
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """Get buyer's current cart contents."""
    return buyer_service.get_cart(conn, user["id"])


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """Place order from cart items and clear cart."""
    return buyer_service.place_order(conn, user["id"])


@router.get("/orders", response_model=List[OrderResponse])
def list_orders(
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """Get buyer's order history with product names."""
    return buyer_service.list_orders(conn, user["id"])
