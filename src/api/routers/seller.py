from sqlite3 import Connection

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.dependencies import get_db_conn, require_seller
from src.shared.models.buyer import ProductResponse
from src.shared.models.seller import ProductCreate, ProductUpdate

router = APIRouter(prefix="/seller", tags=["seller"])


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    user=Depends(require_seller),
    conn: Connection = Depends(get_db_conn),
):
    cursor = conn.execute(
        """
        INSERT INTO products (name, description, price, quantity, seller_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (payload.name, payload.description, payload.price, payload.quantity, user["id"]),
    )

    product_id = cursor.lastrowid

    return {"id": product_id}


@router.get("/products")
def list_own_products(
    user=Depends(require_seller),
    conn: Connection = Depends(get_db_conn),
):
    rows = conn.execute(
        """
        SELECT * FROM products
        WHERE seller_id = ?
        ORDER BY id DESC
        """,
        (user["id"],),
    ).fetchall()

    return [ProductResponse(**dict(row)) for row in rows]


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    user=Depends(require_seller),
    conn: Connection = Depends(get_db_conn),
):
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product["seller_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your product")

    if not payload.model_dump(exclude_unset=True):
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update",
        )

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


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    user=Depends(require_seller),
    conn: Connection = Depends(get_db_conn),
):
    product = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product["seller_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your product")

    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
