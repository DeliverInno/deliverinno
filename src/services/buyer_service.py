from typing import List
from sqlite3 import Connection, OperationalError, IntegrityError, DatabaseError

from fastapi import HTTPException, status

from src.shared.models.buyer import (
    ProductResponse,
    CartItemResponse,
    OrderItemResponse,
    OrderResponse,
    AddToCartRequest,
)


def list_products(conn: Connection) -> List[ProductResponse]:
    """Get all products with stock > 0, ordered by newest first."""
    try:
        # Query all products with available stock
        rows = conn.execute(
            """
            SELECT id, name, description, price, quantity, seller_id
            FROM products
            WHERE quantity > 0
            ORDER BY id DESC
            """
        ).fetchall()

        # Convert database rows to response models
        return [ProductResponse(**dict(row)) for row in rows]

    except (OperationalError, IntegrityError, DatabaseError) as e:
        # Handle database connectivity issues
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )


def add_to_cart(conn: Connection, user_id: int, payload: AddToCartRequest) -> dict:
    """
    Add product to cart with atomic stock reservation.

    Uses atomic UPDATE to prevent race conditions:
    - Decrements stock only if quantity available
    - Upserts cart item (INSERT or UPDATE on conflict)
    """
    try:
        # STEP 1: Atomically decrease product quantity only if sufficient stock exists
        # This UPDATE only succeeds if products.quantity >= payload.quantity
        cur = conn.execute(
            """
            UPDATE products
            SET quantity = quantity - ?
            WHERE id = ? AND quantity >= ?
            """,
            (payload.quantity, payload.product_id, payload.quantity),
        )

        # Check if UPDATE succeeded (rowcount > 0 means stock was reserved)
        if cur.rowcount == 0:
            # Stock reservation failed - check if product exists at all
            product = conn.execute(
                "SELECT id, quantity FROM products WHERE id = ?",
                (payload.product_id,),
            ).fetchone()

            if product is None:
                # Product doesn't exist in database
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found",
                )

            # Product exists but not enough stock available
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Not enough stock",
            )

        # STEP 2: Add or update item in shopping cart
        # ON CONFLICT clause handles case where item already in cart
        # If item exists, increase quantity; if new, insert new row
        conn.execute(
            """
            INSERT INTO cart_items (user_id, product_id, quantity)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, product_id)
            DO UPDATE SET quantity = quantity + excluded.quantity
            """,
            (user_id, payload.product_id, payload.quantity),
        )

        return {"status": "ok"}

    except HTTPException:
        # Re-raise application errors (404, 400, 503)
        raise
    except (OperationalError, IntegrityError, DatabaseError) as e:
        # Handle unexpected database errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )


def get_cart(conn: Connection, user_id: int) -> List[CartItemResponse]:
    """Get cart items with product details (name, price). Complexity: O(n)."""
    try:
        # Query cart items with product details joined from products table
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

        # Convert database rows to response models
        return [CartItemResponse(**dict(row)) for row in rows]

    except (OperationalError, IntegrityError, DatabaseError) as e:
        # Handle database connectivity issues
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )


def place_order(conn: Connection, user_id: int) -> OrderResponse:
    """
    Create order from cart: validate → calculate total → insert order & items → clear cart.

    Stock is pre-reserved in add_to_cart, so this only creates order records.
    """
    try:
        # STEP 1: Fetch all cart items with current product prices
        cart_rows = conn.execute(
            """
            SELECT ci.product_id, ci.quantity, p.price, p.name
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            """,
            (user_id,),
        ).fetchall()

        # Validate cart contains items
        if not cart_rows:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty",
            )

        # STEP 2: Calculate total order amount (quantity * price per item)
        total = sum(row["quantity"] * row["price"] for row in cart_rows)

        # STEP 3: Insert order header and get order ID
        cursor = conn.execute(
            """
            INSERT INTO orders (user_id, total_amount, status)
            VALUES (?, ?, 'pending')
            """,
            (user_id, total),
        )
        order_id = cursor.lastrowid

        # Validate order was created successfully
        if order_id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create order",
            )

        order_id = int(order_id)

        # STEP 4: Insert all cart items into order_items table
        # This records the price at time of order (prices may change later)
        for row in cart_rows:
            conn.execute(
                """
                INSERT INTO order_items (order_id, product_id, quantity, price_at_time)
                VALUES (?, ?, ?, ?)
                """,
                (order_id, row["product_id"], row["quantity"], row["price"]),
            )

        # STEP 5: Clear buyer's cart after successful order placement
        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))

        # STEP 6: Fetch order items with product names for response
        items_with_names = conn.execute(
            """
            SELECT oi.product_id, oi.quantity, oi.price_at_time, p.name
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            """,
            (order_id,),
        ).fetchall()

        # STEP 7: Return complete order response
        return OrderResponse(
            id=order_id,
            total_amount=total,
            status="pending",
            items=[OrderItemResponse(**dict(item)) for item in items_with_names],
        )

    except HTTPException:
        # Re-raise application errors (400, 500, 503)
        raise
    except (OperationalError, IntegrityError, DatabaseError) as e:
        # Handle unexpected database errors
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )


def list_orders(conn: Connection, user_id: int) -> List[OrderResponse]:
    """Get all orders with items for user, newest first. Complexity: O(n*m)."""
    try:
        # STEP 1: Fetch all orders for user, newest first
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

        # STEP 2: For each order, fetch all associated items
        for order in orders:
            # Fetch items with product names for this specific order
            items = conn.execute(
                """
                SELECT oi.product_id, oi.quantity, oi.price_at_time, p.name
                FROM order_items oi
                JOIN products p ON p.id = oi.product_id
                WHERE oi.order_id = ?
                """,
                (order["id"],),
            ).fetchall()

            # Create OrderResponse with all items
            results.append(
                OrderResponse(
                    id=order["id"],
                    total_amount=order["total_amount"],
                    status=order["status"],
                    items=[OrderItemResponse(**dict(item)) for item in items],
                )
            )

        return results

    except (OperationalError, IntegrityError, DatabaseError) as e:
        # Handle database connectivity issues
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )
