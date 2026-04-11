from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """
    Request payload for creating a new product by seller.

    Validates:
    - name: Required, 1–100 characters
    - price: Must be non-negative
    - quantity: Must be non-negative
    - description: Optional
    """

    name: str = Field(
        min_length=1,
        max_length=100,
        description="Product name"
    )
    description: str | None = Field(
        default=None,
        description="Optional product description"
    )
    price: float = Field(
        ge=0,
        description="Product price (>= 0)"
    )
    quantity: int = Field(
        ge=0,
        description="Initial stock quantity (>= 0)"
    )


class ProductUpdate(BaseModel):
    """
    Request payload for updating an existing product.

    All fields are optional:
    - Only provided fields will be updated
    - Validation ensures non-negative price and quantity
    """

    name: str | None = Field(
        default=None,
        description="New product name"
    )
    description: str | None = Field(
        default=None,
        description="New product description"
    )
    price: float | None = Field(
        default=None,
        ge=0,
        description="New product price (>= 0)"
    )
    quantity: int | None = Field(
        default=None,
        ge=0,
        description="New stock quantity (>= 0)"
    )
