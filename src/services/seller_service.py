from sqlite3 import Connection
from fastapi import HTTPException

from src.shared.models.seller import ProductCreate, ProductUpdate
from src.shared.models.buyer import ProductResponse


def create_product(conn: Connection, user_id: int, payload: ProductCreate) -> dict:
    cursor = conn.execute(
        """
        INSERT INTO products (name, description, price, quantity, seller_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (payload.name, payload.description, payload.price, payload.quantity, user_id),
    )

    product_id = cursor.lastrowid
    return {"id": int(product_id)}


def list_products(conn: Connection, user_id: int):
    rows = conn.execute(
        """
        SELECT * FROM products
        WHERE seller_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    ).fetchall()

    return [ProductResponse(**dict(row)) for row in rows]


def update_product(conn: Connection, user_id: int, product_id: int, payload: ProductUpdate):
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product["seller_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your product")

    update_data = payload.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    conn.execute(
        """
        UPDATE products
        SET name = COALESCE(?, name),
            description = COALESCE(?, description),
            price = COALESCE(?, price),
            quantity = COALESCE(?, quantity)
        WHERE id = ?
        """,
        (
            payload.name,
            payload.description,
            payload.price,
            payload.quantity,
            product_id,
        ),
    )

    return {"status": "updated"}


def delete_product(conn: Connection, user_id: int, product_id: int):
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product["seller_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not your product")

    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
