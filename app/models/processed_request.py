from datetime import datetime

from sqlalchemy import JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ProcessedRequest(Base):
    """
    Stores processed request IDs for idempotency.
    
    When a client sends a request with a request_id that has already been
    processed, we return the cached response instead of processing again.
    """

    __tablename__ = "processed_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    response_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    date_created: Mapped[datetime] = mapped_column(
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ProcessedRequest(id={self.id}, request_id='{self.request_id}')>"
