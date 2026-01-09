from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServiceOrderImageResponse(BaseModel):
    """Schema for service order image response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    file_name: str
    image_url: str
    date_created: datetime
    date_updated: datetime | None
