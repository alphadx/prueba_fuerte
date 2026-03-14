from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.ecommerce import PickupSlot, OnlineOrder, OrderLine
from app.schemas.ecommerce import (
    PickupSlotCreate, PickupSlotOut,
    OnlineOrderCreate, OnlineOrderStatusUpdate, OnlineOrderOut,
)

router = APIRouter(tags=["ecommerce"])


# ---- Pickup Slots ----

@router.get("/pickup-slots", response_model=List[PickupSlotOut])
async def list_pickup_slots(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(PickupSlot))
    return result.scalars().all()


@router.post("/pickup-slots", response_model=PickupSlotOut, status_code=201)
async def create_pickup_slot(
    payload: PickupSlotCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = PickupSlot(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ---- Orders ----

@router.post("/orders", response_model=OnlineOrderOut, status_code=201)
async def create_order(
    payload: OnlineOrderCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    total = sum(line.unit_price * line.quantity for line in payload.lines)
    order = OnlineOrder(
        branch_id=payload.branch_id,
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        customer_phone=payload.customer_phone,
        delivery_type=payload.delivery_type,
        pickup_slot_id=payload.pickup_slot_id,
        total=total,
        status="received",
    )
    db.add(order)
    await db.flush()

    for line_data in payload.lines:
        subtotal = (line_data.unit_price * line_data.quantity).quantize(Decimal("0.01"))
        line = OrderLine(
            order_id=order.id,
            product_id=line_data.product_id,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            subtotal=subtotal,
        )
        db.add(line)

    # Increment pickup slot counter
    if payload.pickup_slot_id:
        slot_result = await db.execute(
            select(PickupSlot).where(PickupSlot.id == payload.pickup_slot_id)
        )
        slot = slot_result.scalar_one_or_none()
        if slot:
            slot.current_orders += 1

    await db.flush()
    result = await db.execute(
        select(OnlineOrder)
        .options(selectinload(OnlineOrder.lines))
        .where(OnlineOrder.id == order.id)
    )
    return result.scalar_one()


@router.get("/orders/{order_id}", response_model=OnlineOrderOut)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(OnlineOrder)
        .options(selectinload(OnlineOrder.lines))
        .where(OnlineOrder.id == order_id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    return obj


@router.put("/orders/{order_id}/status", response_model=OnlineOrderOut)
async def update_order_status(
    order_id: int,
    payload: OnlineOrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    valid_statuses = {"received", "prepared", "ready", "delivered"}
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid_statuses}")
    result = await db.execute(
        select(OnlineOrder)
        .options(selectinload(OnlineOrder.lines))
        .where(OnlineOrder.id == order_id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Order not found")
    obj.status = payload.status
    await db.flush()
    await db.refresh(obj)
    return obj
