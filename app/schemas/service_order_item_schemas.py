from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from schemas.spare_part_schemas import SparePartResponse


class ServiceOrderItemCreate(BaseModel):
    """Schema for creating a service order item."""

    spare_part_id: int
    quantity: int = Field(..., gt=0)


class ServiceOrderItemResponse(BaseModel):
    """Schema for service order item response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    spare_part_id: int
    quantity: int
    unit_price: Decimal
    spare_part: SparePartResponse
    date_created: datetime
    date_updated: datetime | None
