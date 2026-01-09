from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=255)


class CategoryResponse(BaseModel):
    """Schema for category response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    date_created: datetime
    date_updated: datetime | None
