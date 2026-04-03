from sqlite3 import Connection

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.dependencies import get_db_conn, require_seller

router = APIRouter(prefix="/seller", tags=["seller"])


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    price: float = Field(ge=0)
    quantity: int = Field(ge=0)


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=0)


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

    return [dict(row) for row in rows]


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

    update_fields = []
    values = []

    for field, value in payload.dict(exclude_unset=True).items():
        update_fields.append(f"{field} = ?")
        values.append(value)

    if update_fields:
        values.append(product_id)
        conn.execute(
            f"UPDATE products SET {', '.join(update_fields)} WHERE id = ?",
            values,
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
