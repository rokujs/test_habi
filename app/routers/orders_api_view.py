from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from core.decorators import measure_time
from models.service_order import ServiceOrder, ServiceOrderStatus
from models.service_order_item import ServiceOrderItem
from models.spare_part import SparePart
from schemas.service_order_schemas import ServiceOrderCreate, ServiceOrderResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post(
    "/",
    response_model=ServiceOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
@measure_time
def create_service_order(
    order_data: ServiceOrderCreate,
    db: Session = Depends(get_db),
) -> ServiceOrder:
    """
    Create a new service order (idempotent).

    If a request with the same **request_id** was already processed,
    the existing order is returned instead of creating a duplicate.

    - **request_id**: Unique identifier for idempotency
    - **items**: List of spare parts with quantities
    """
    # Check for existing order with same request_id (idempotency)
    # Only return existing order if created within the idempotency window
    idempotency_threshold = datetime.now(timezone.utc) - timedelta(
        seconds=ServiceOrder.IDEMPOTENCY_WINDOW_SECONDS
    )
    existing_order = db.execute(
        select(ServiceOrder).where(
            ServiceOrder.request_id == order_data.request_id,
            ServiceOrder.date_created >= idempotency_threshold,
        )
    ).scalar_one_or_none()

    if existing_order is not None:
        # Return existing order without creating a new one
        return existing_order

    # Validate all spare parts exist and get their prices
    spare_part_ids = [item.spare_part_id for item in order_data.items]
    spare_parts = (
        db.execute(select(SparePart).where(SparePart.id.in_(spare_part_ids)))
        .scalars()
        .all()
    )

    spare_parts_map = {sp.id: sp for sp in spare_parts}

    # Check if all requested spare parts exist
    missing_ids = set(spare_part_ids) - set(spare_parts_map.keys())
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spare parts not found: {list(missing_ids)}",
        )

    # Check stock availability
    for item in order_data.items:
        spare_part = spare_parts_map[item.spare_part_id]
        if spare_part.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{spare_part.name}' (SKU: {spare_part.sku}). "
                f"Available: {spare_part.stock}, Requested: {item.quantity}",
            )

    # Create the order
    order = ServiceOrder(
        request_id=order_data.request_id,
        status=ServiceOrderStatus.PENDING,
        total=Decimal("0.00"),
    )
    db.add(order)
    db.flush()  # Get the order ID

    # Create order items and calculate total
    total = Decimal("0.00")
    for item_data in order_data.items:
        spare_part = spare_parts_map[item_data.spare_part_id]
        unit_price = spare_part.price
        item_total = unit_price * item_data.quantity

        order_item = ServiceOrderItem(
            order_id=order.id,
            spare_part_id=item_data.spare_part_id,
            quantity=item_data.quantity,
            unit_price=unit_price,
        )
        db.add(order_item)

        # Reduce stock
        spare_part.stock -= item_data.quantity

        total += item_total

    order.total = total
    db.commit()
    db.refresh(order)

    return order
