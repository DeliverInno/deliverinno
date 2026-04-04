"""Buyer API endpoints for browsing products, managing cart and orders."""

from typing import List
from sqlite3 import Connection

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_db_conn, require_buyer
from src.shared.models.buyer import (
    ProductResponse,
    CartItemResponse,
    OrderItemResponse,
    OrderResponse,
    AddToCartRequest,
)

router = APIRouter(prefix="/buyer", tags=["buyer"])


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
    Add product to buyer's cart and decrease product quantity.

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

    # Decrease product quantity in catalog
    conn.execute(
        "UPDATE products SET quantity = quantity - ? WHERE id = ?",
        (payload.quantity, payload.product_id),
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
    clears cart. Product quantities already decreased when added to cart.

    Args:
        user: Current buyer (from X-User-Id header)
        conn: Database connection

    Returns:
        Created order with items and total

    Raises:
        400: Cart is empty
    """
    cart_rows = conn.execute(
        """
        SELECT ci.product_id, ci.quantity, p.price, p.name
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

    total = sum(row["quantity"] * row["price"] for row in cart_rows)
    cursor = conn.execute(
        """
        INSERT INTO orders (user_id, total_amount, status)
        VALUES (?, ?, 'pending')
        """,
        (user["id"], total),
    )
    order_id = cursor.lastrowid

    if order_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order",
        )

    order_id = int(order_id)

    # Insert order items
    for row in cart_rows:
        conn.execute(
            """
            INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
            VALUES (?, ?, ?, ?)
            """,
            (order_id, row["product_id"], row["quantity"], row["price"]),
        )

    conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user["id"],))

    # Fetch items with names for response
    items_with_names = conn.execute(
        """
        SELECT oi.product_id, oi.quantity, oi.price_at_time, p.name
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = ?
        """,
        (order_id,),
    ).fetchall()

    return OrderResponse(
        id=order_id,
        total_amount=total,
        status="pending",
        items=[
            OrderItemResponse(**dict(item)) for item in items_with_names
        ],
    )


@router.get("/orders", response_model=List[OrderResponse])
def list_orders(
    user=Depends(require_buyer),
    conn: Connection = Depends(get_db_conn),
):
    """
    Get buyer's order history with product names.

    Args:
        user: Current buyer (from X-User-Id header)
        conn: Database connection

    Returns:
        List of orders with items (including product names), newest first
    """
    orders = conn.execute(
        """
        SELECT id, total_amount, status
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user["id"],),
    ).fetchall()

    results: List[OrderResponse] = []
    for order in orders:
        items = conn.execute(
            """
            SELECT oi.product_id, oi.quantity, oi.price_at_time, p.name
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
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
