from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""

    name: str
    description: str | None = None


class CategoryResponse(BaseModel):
    """Schema for category response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    date_created: datetime
    date_updated: datetime | None
