from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from schemas.service_order_item_schemas import ServiceOrderItemCreate, ServiceOrderItemResponse


class ServiceOrderCreate(BaseModel):
    """Schema for creating a new service order."""

    request_id: int = Field(..., gt=0)
    items: list[ServiceOrderItemCreate] = Field(..., min_length=1)


class ServiceOrderResponse(BaseModel):
    """Schema for service order response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    status: str
    total: Decimal
    items: list[ServiceOrderItemResponse]
    date_created: datetime
    date_updated: datetime | None
