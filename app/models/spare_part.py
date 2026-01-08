from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.auditor import Auditor


class SparePart(Auditor):
    """Spare part model for maintenance items/replacements."""

    __tablename__ = "spare_parts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(default=0, nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    category: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="spare_parts",
        lazy="joined",
    )

    # B-Tree index on SKU column (PostgreSQL default index type is B-Tree)
    __table_args__ = (
        Index("ix_spare_parts_sku_btree", "sku", postgresql_using="btree"),
    )

    def __repr__(self) -> str:
        return f"<SparePart(id={self.id}, name='{self.name}', sku='{self.sku}')>"
