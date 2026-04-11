from sqlite3 import Connection, OperationalError, IntegrityError, DatabaseError
from fastapi import HTTPException, status

from src.shared.models.seller import ProductCreate, ProductUpdate
from src.shared.models.buyer import ProductResponse


def create_product(conn: Connection, user_id: int, payload: ProductCreate) -> dict:
    """
    Create a new product in the database.

    Returns:
    - id of newly created product
    """
    try:
        cursor = conn.execute(
            """
            INSERT INTO products (name, description, price, quantity, seller_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.name, payload.description, payload.price, payload.quantity, user_id),
        )

        product_id = cursor.lastrowid
        return {"id": int(product_id)}

    except (OperationalError, IntegrityError, DatabaseError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )


def list_products(conn: Connection, user_id: int):
    """
    Get all products for a specific seller.

    Ordered by newest first.
    """
    try:
        rows = conn.execute(
            """
            SELECT * FROM products
            WHERE seller_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        ).fetchall()

        return [ProductResponse(**dict(row)) for row in rows]

    except (OperationalError, IntegrityError, DatabaseError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )


def update_product(conn: Connection, user_id: int, product_id: int, payload: ProductUpdate):
    """
    Update product fields for a seller.

    Steps:
    - Validate product exists
    - Validate ownership
    - Apply partial update
    """
    try:
        # STEP 1: Fetch product
        product = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # STEP 2: Check ownership
        if product["seller_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your product"
            )

        # STEP 3: Extract only provided fields
        update_data = payload.model_dump(exclude_unset=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update"
            )

        # STEP 4: Perform update using COALESCE for partial updates
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

    except HTTPException:
        raise
    except (OperationalError, IntegrityError, DatabaseError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )


def delete_product(conn: Connection, user_id: int, product_id: int):
    """
    Delete a product owned by seller.

    Steps:
    - Validate product exists
    - Validate ownership
    - Delete product
    """
    try:
        # STEP 1: Fetch product
        product = conn.execute(
            "SELECT * FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # STEP 2: Check ownership
        if product["seller_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your product"
            )

        # STEP 3: Delete product
        conn.execute(
            "DELETE FROM products WHERE id = ?",
            (product_id,)
        )

    except HTTPException:
        raise
    except (OperationalError, IntegrityError, DatabaseError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {e}",
        )
