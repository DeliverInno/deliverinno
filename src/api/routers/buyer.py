"""Buyer API endpoints for browsing products, managing cart and orders."""

from typing import List
from sqlite3 import Connection

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_db_conn, require_buyer


router = APIRouter(prefix="/buyer", tags=["buyer"])


class AddToCartRequest(BaseModel):
    """Request model for adding item to cart."""

    product_id: int = Field(gt=0, description="Product ID")
    quantity: int = Field(gt=0, description="Quantity to add")


class CartItemResponse(BaseModel):
    """Response model for a single cart item."""

    product_id: int
    name: str
    price: float
    quantity: int

    class Config:
        from_attributes = True


class OrderItemResponse(BaseModel):
    """Response model for item in completed order."""

    product_id: int
    quantity: int
    price_at_time: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Response model for a completed order."""

    id: int
    total_amount: float
    status: str
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    """Response model for a product."""

    id: int
    name: str
    description: str | None
    price: float
    quantity: int
    seller_id: int

    class Config:
        from_attributes = True


@router.get("/products", response_model=List[ProductResponse])
def list_products(conn: Connection = Depends(get_db_conn)):
    """
    Get all available products with quantity > 0.

    Returns:
        List of products ordered by newest first.
    """
    rows = conn.execute(
        """
        SELECT id, name, description, price, quantity, seller_id
        FROM products
        WHERE quantity > 0
        ORDER BY id DESC
        """
    ).fetchall()
    return [ProductResponse(**dict(row)) for row in rows]


@router.post("/cart", status_code=status.HTTP_201_CREATED)
def add_to_cart(
    payload: AddToCartRequest,
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """
    Add product to buyer's cart.

    Args:
        payload: Product ID and quantity to add
        user: Current buyer (from X-User-Id header)
        conn: Database connection

    Returns:
        Status confirmation

    Raises:
        404: Product not found
        400: Not enough stock
    """
    product = conn.execute(
        "SELECT id, quantity FROM products WHERE id = ?",
        (payload.product_id,),
    ).fetchone()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if payload.quantity > product["quantity"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough stock",
        )

    conn.execute(
        """
        INSERT INTO cart_items (user_id, product_id, quantity)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, product_id)
        DO UPDATE SET quantity = quantity + excluded.quantity
        """,
        (user["id"], payload.product_id, payload.quantity),
    )

    return {"status": "ok"}


@router.get("/cart", response_model=List[CartItemResponse])
def get_cart(
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """
    Get buyer's current cart contents.

    Args:
        user: Current buyer (from X-User-Id header)
        conn: Database connection

    Returns:
        List of items in cart with product details
    """
    rows = conn.execute(
        """
        SELECT ci.product_id, p.name, p.price, ci.quantity
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = ?
        ORDER BY ci.added_at DESC
        """,
        (user["id"],),
    ).fetchall()

    return [CartItemResponse(**dict(row)) for row in rows]


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def place_order(
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """
    Place order from cart items.

    Validates stock, creates order record, copies cart items to order_items,
    decreases product quantities, clears cart.

    Args:
        user: Current buyer (from X-User-Id header)
        conn: Database connection

    Returns:
        Created order with items and total

    Raises:
        400: Cart is empty or not enough stock
    """
    cart_rows = conn.execute(
        """
        SELECT ci.product_id, ci.quantity, p.price, p.quantity AS stock
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = ?
        """,
        (user["id"],),
    ).fetchall()

    if not cart_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty",
        )

    for row in cart_rows:
        if row["quantity"] > row["stock"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough stock for product {row['product_id']}",
            )

    total = sum(row["quantity"] * row["price"] for row in cart_rows)
    cursor = conn.execute(
        "INSERT INTO orders (user_id, total_amount, status) VALUES (?, ?, 'pending')",
        (user["id"], total),
    )
    order_id = cursor.lastrowid

    if order_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )

    order_id = int(order_id)

    for row in cart_rows:
        conn.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, row["product_id"], row["quantity"], row["price"]),
        )
        conn.execute(
            "UPDATE products SET quantity = quantity - ? WHERE id = ?",
            (row["quantity"], row["product_id"]),
        )

    conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user["id"],))

    return OrderResponse(
        id=order_id,
        total_amount=total,
        status="pending",
        items=[
            OrderItemResponse(
                product_id=row["product_id"],
                quantity=row["quantity"],
                price_at_time=row["price"],
            )
            for row in cart_rows
        ],
    )


@router.get("/orders", response_model=List[OrderResponse])
def list_orders(
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """
    Get buyer's order history.

    Args:
        user: Current buyer (from X-User-Id header)
        conn: Database connection

    Returns:
        List of orders with items, newest first
    """
    orders = conn.execute(
        "SELECT id, total_amount, status FROM orders WHERE user_id = ? ORDER BY id DESC",
        (user["id"],),
    ).fetchall()

    results: List[OrderResponse] = []
    for order in orders:
        items = conn.execute(
            """
            SELECT product_id, quantity, price_at_time
            FROM order_items
            WHERE order_id = ?
            """,
            (order["id"],),
        ).fetchall()
        results.append(
            OrderResponse(
                id=order["id"],
                total_amount=order["total_amount"],
                status=order["status"],
                items=[OrderItemResponse(**dict(item)) for item in items],
            )
        )

    return results
