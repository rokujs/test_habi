from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from models.category import Category
from schemas.category import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
) -> Category:
    """
    Create a new category.

    - **name**: Name of the category
    - **description**: Optional description of the category
    """
    # Check if category with same name already exists
    existing = db.execute(
        select(Category).where(Category.name == category_data.name)
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category_data.name}' already exists",
        )

    category = Category(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)

    return category
