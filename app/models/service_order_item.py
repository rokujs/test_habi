from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.auditor import Auditor


class ServiceOrderItem(Auditor):
    """Line item for service orders."""

    __tablename__ = "service_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("service_orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    spare_part_id: Mapped[int] = mapped_column(
        ForeignKey("spare_parts.id", ondelete="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Relationships
    order: Mapped["ServiceOrder"] = relationship(
        "ServiceOrder",
        back_populates="items",
    )
    spare_part: Mapped["SparePart"] = relationship(
        "SparePart",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<ServiceOrderItem(id={self.id}, order_id={self.order_id}, quantity={self.quantity})>"
