"""Buyer business logic services."""

from typing import List
from sqlite3 import Connection

from fastapi import HTTPException, status

from src.shared.models.buyer import (
    ProductResponse,
    CartItemResponse,
    OrderItemResponse,
    OrderResponse,
    AddToCartRequest,
)


def list_products(conn: Connection) -> List[ProductResponse]:
    rows = conn.execute(
        """
        SELECT id, name, description, price, quantity, seller_id
        FROM products
        WHERE quantity > 0
        ORDER BY id DESC
        """
    ).fetchall()
    return [ProductResponse(**dict(row)) for row in rows]


def add_to_cart(conn: Connection, user_id: int, payload: AddToCartRequest) -> dict:
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
        (user_id, payload.product_id, payload.quantity),
    )

    conn.execute(
        "UPDATE products SET quantity = quantity - ? WHERE id = ?",
        (payload.quantity, payload.product_id),
    )

    return {"status": "ok"}


def get_cart(conn: Connection, user_id: int) -> List[CartItemResponse]:
    rows = conn.execute(
        """
        SELECT ci.product_id, p.name, p.price, ci.quantity
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = ?
        ORDER BY ci.added_at DESC
        """,
        (user_id,),
    ).fetchall()

    return [CartItemResponse(**dict(row)) for row in rows]


def place_order(conn: Connection, user_id: int) -> OrderResponse:
    cart_rows = conn.execute(
        """
        SELECT ci.product_id, ci.quantity, p.price, p.name
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = ?
        """,
        (user_id,),
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
        (user_id, total),
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

    conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

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
        items=[OrderItemResponse(**dict(item)) for item in items_with_names],
    )


def list_orders(conn: Connection, user_id: int) -> List[OrderResponse]:
    orders = conn.execute(
        """
        SELECT id, total_amount, status
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
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
