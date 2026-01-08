from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.auditor import Auditor


class Category(Auditor):
    """Category model for classifying spare parts."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    spare_parts: Mapped[list["SparePart"]] = relationship(
        "SparePart",
        back_populates="category",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"
