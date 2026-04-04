from typing import List
from pydantic import BaseModel, Field


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
    name: str

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
