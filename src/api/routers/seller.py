from fastapi import APIRouter, Depends, status
from sqlite3 import Connection

from src.api.dependencies import get_db_conn, require_seller
from src.services import seller_service
from src.shared.models.seller import ProductCreate, ProductUpdate
from src.shared.models.buyer import ProductResponse

router = APIRouter(prefix="/seller", tags=["seller"])


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    user=Depends(require_seller),
    conn: Connection = Depends(get_db_conn),
):
    return seller_service.create_product(conn, user["id"], payload)


@router.get("/products", response_model=list[ProductResponse])
def list_products(
    user=Depends(require_seller),
    conn: Connection = Depends(get_db_conn),
):
    return seller_service.list_products(conn, user["id"])


@router.put("/products/{product_id}")
def update_product(
    product_id: int,
    payload: ProductUpdate,
    user=Depends(require_seller),
    conn: Connection = Depends(get_db_conn),
):
    return seller_service.update_product(conn, user["id"], product_id, payload)


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    user=Depends(require_seller),
    conn: Connection = Depends(get_db_conn),
):
    seller_service.delete_product(conn, user["id"], product_id)
