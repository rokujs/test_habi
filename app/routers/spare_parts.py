from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.utils import validate_sku_format
from models.spare_part import SparePart
from schemas.spare_part import SparePartCreate, SparePartResponse

router = APIRouter(prefix="/items", tags=["Items"])


@router.post(
    "/",
    response_model=SparePartResponse,
    status_code=status.HTTP_201_CREATED,
)
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
