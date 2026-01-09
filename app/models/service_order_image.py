from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.auditor import Auditor


class ServiceOrderImage(Auditor):
    """Image associated with a service order to track progress."""

    __tablename__ = "service_order_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("service_orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Relationships
    order: Mapped["ServiceOrder"] = relationship(
        "ServiceOrder",
        back_populates="images",
    )

    def __repr__(self) -> str:
        return f"<ServiceOrderImage(id={self.id}, order_id={self.order_id}, file_name='{self.file_name}')>"
