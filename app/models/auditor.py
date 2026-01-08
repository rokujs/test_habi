from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Auditor(Base):
    """Abstract base class with audit fields for all models."""

    __abstract__ = True

    date_created: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    date_updated: Mapped[datetime | None] = mapped_column(
        default=None,
        onupdate=func.now(),
        server_onupdate=func.now(),
        nullable=True,
    )
