from core.decorators import measure_time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from core.database import get_db
from core.utils import validate_sku_format
from models.spare_part import SparePart
from schemas.spare_part_schemas import SparePartCreate, SparePartResponse, SparePartUpdate

router = APIRouter(prefix="/items", tags=["Items"])


@router.post(
    "/",
    response_model=SparePartResponse,
    status_code=status.HTTP_201_CREATED,
)
@measure_time
def create_spare_part(
    spare_part_data: SparePartCreate,
    db: Session = Depends(get_db),
) -> SparePart:
    """
    Register a new spare part.

    - **name**: Name of the spare part
    - **sku**: Unique stock keeping unit identifier with format [CLASS]-[MATERIAL]-[SIZE]-[LENGTH]
    - **price**: Unit price
    - **stock**: Available quantity in inventory
    - **category_id**: Optional category reference
    """
    # Validate SKU structure
    is_valid, error_message = validate_sku_format(spare_part_data.sku)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message,
        )
    
    # Check if SKU already exists
    existing = db.execute(
        select(SparePart).where(SparePart.sku == spare_part_data.sku)
    ).scalar_one_or_none()

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Spare part with SKU '{spare_part_data.sku}' already exists",
        )

    spare_part = SparePart(**spare_part_data.model_dump())

    db.add(spare_part)
    db.commit()
    db.refresh(spare_part)

    return spare_part


@router.patch("/{sku}", response_model=SparePartResponse)
@measure_time
def update_spare_part(
    sku: str,
    spare_part_data: SparePartUpdate,
    db: Session = Depends(get_db),
) -> SparePart:
    """
    Partial update of a spare part by SKU.

    Only **price** and **stock** can be updated.
    Fields not provided will remain unchanged.
    """
    spare_part = db.execute(
        select(SparePart)
        .options(joinedload(SparePart.category))
        .where(SparePart.sku == sku)
    ).scalar_one_or_none()

    if spare_part is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spare part with SKU '{sku}' not found",
        )

    # Only update fields that were provided (partial update)
    update_data = spare_part_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update provided",
        )

    for field, value in update_data.items():
        setattr(spare_part, field, value)
    db.commit()
    db.refresh(spare_part)

    return spare_part


@router.get("/", response_model=list[SparePartResponse])
@measure_time
def list_spare_parts(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> list[SparePart]:
    """
    List all spare parts with their categories (LEFT JOIN).

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    """
    stmt = (
        select(SparePart)
        .options(joinedload(SparePart.category))
        .offset(skip)
        .limit(limit)
    )
    result = db.execute(stmt).scalars().unique().all()
    return list(result)
