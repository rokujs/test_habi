from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from schemas.category_schemas import CategoryResponse


class SparePartCreate(BaseModel):
    """Schema for creating a new spare part."""

    name: str = Field(..., min_length=1, max_length=150)
    sku: str = Field(..., min_length=1, max_length=50)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    category_id: int | None = None


class SparePartResponse(BaseModel):
    """Schema for spare part response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    price: Decimal
    stock: int
    category_id: int | None
    category: CategoryResponse | None
    date_created: datetime
    date_updated: datetime | None


class SparePartUpdate(BaseModel):
    """Schema for partial update of a spare part (PATCH)."""

    price: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
