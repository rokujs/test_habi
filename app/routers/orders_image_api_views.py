from uuid import uuid4

from fastapi import Depends, File, HTTPException, UploadFile, status, APIRouter
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.decorators import measure_time
from models.service_order import ServiceOrder
from models.service_order_image import ServiceOrderImage
from schemas.service_order_image_schema import ServiceOrderImageResponse
from services.s3_service import S3UploadError, s3_service


router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/{order_id}/image/",
    response_model=ServiceOrderImageResponse,
    status_code=status.HTTP_201_CREATED,
)
@measure_time
def upload_order_image(
    order_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ServiceOrderImage:
    """
    Upload an image to track service order progress.

    - **order_id**: ID of the service order
    - **file**: Image file to upload
    """
    # Verify order exists
    order = db.execute(
        select(ServiceOrder).where(ServiceOrder.id == order_id)
    ).scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service order with ID '{order_id}' not found",
        )

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )

    # Generate unique filename
    extension = file.filename.split(".")[-1] if file.filename else "jpg"
    unique_filename = f"orders/{order_id}/{uuid4()}.{extension}"

    try:
        # Upload to S3
        image_url = s3_service.upload_image(
            file_content=file.file,
            file_name=unique_filename,
            content_type=file.content_type or "image/jpeg",
        )

        # Save to database
        image = ServiceOrderImage(
            order_id=order_id,
            file_name=file.filename or unique_filename,
            image_url=image_url,
        )
        db.add(image)
        db.commit()
        db.refresh(image)

    except S3UploadError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload image: {str(e)}",
        )

    return image


@router.get(
    "/{order_id}/images/",
    response_model=list[ServiceOrderImageResponse],
)
@measure_time
def list_order_images(
    order_id: int,
    db: Session = Depends(get_db),
) -> list[ServiceOrderImage]:
    """
    List all images for a service order.

    - **order_id**: ID of the service order
    """
    # Verify order exists
    order = db.execute(
        select(ServiceOrder).where(ServiceOrder.id == order_id)
    ).scalar_one_or_none()

    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service order with ID '{order_id}' not found",
        )

    images = (
        db.execute(
            select(ServiceOrderImage).where(ServiceOrderImage.order_id == order_id)
        )
        .scalars()
        .all()
    )

    return list(images)
