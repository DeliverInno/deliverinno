from typing import List
from pydantic import BaseModel, Field, ConfigDict


class AddToCartRequest(BaseModel):
    """
    Request payload for adding item to shopping cart.

    Validates:
    - product_id: Must be positive integer
    - quantity: Must be positive integer
    """

    product_id: int = Field(
        gt=0,
        description="Product ID to add to cart"
    )
    quantity: int = Field(
        gt=0,
        description="Number of items to add"
    )


class CartItemResponse(BaseModel):
    """
    Single item in buyer's shopping cart.

    Returned by GET /buyer/cart endpoint.
    Includes current product price and quantity in cart.
    """

    product_id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
    price: float = Field(description="Current product price")
    quantity: int = Field(description="Quantity in cart")

    model_config = ConfigDict(from_attributes=True)


class OrderItemResponse(BaseModel):
    """
    Single item in a completed order.

    Records the price_at_time (snapshot when order was placed).
    Prices may change later, but order preserves historical prices.
    """

    product_id: int = Field(description="Product ID")
    quantity: int = Field(description="Quantity ordered")
    price_at_time: float = Field(description="Price at time of order")
    name: str = Field(description="Product name at time of order")

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """
    Complete order with all items and total amount.

    Returned by POST /buyer/orders (place order) and GET /buyer/orders (history).
    Status values: 'pending', 'confirmed', 'shipped', 'delivered', 'cancelled'
    """

    id: int = Field(description="Order ID")
    total_amount: float = Field(description="Order total amount")
    status: str = Field(description="Order status")
    items: List[OrderItemResponse] = Field(description="Items in this order")

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    """
    Product from catalog available for purchase.

    Returned by GET /buyer/products endpoint.
    Only includes products with quantity > 0.
    """

    id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
    description: str | None = Field(description="Product description")
    price: float = Field(description="Product price")
    quantity: int = Field(description="Available stock quantity")
    seller_id: int = Field(description="Seller's user ID")

    model_config = ConfigDict(from_attributes=True)
