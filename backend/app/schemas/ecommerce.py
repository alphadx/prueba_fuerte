from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel


# ---- PickupSlot ----

class PickupSlotCreate(BaseModel):
    branch_id: int
    date: date
    start_time: str
    end_time: str
    max_orders: int = 10


class PickupSlotOut(BaseModel):
    id: int
    branch_id: int
    date: date
    start_time: str
    end_time: str
    max_orders: int
    current_orders: int

    model_config = {"from_attributes": True}


# ---- OrderLine ----

class OrderLineCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal


class OrderLineOut(BaseModel):
    id: int
    order_id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


# ---- OnlineOrder ----

class OnlineOrderCreate(BaseModel):
    branch_id: int
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_type: str = "pickup"
    pickup_slot_id: Optional[int] = None
    lines: List[OrderLineCreate]


class OnlineOrderStatusUpdate(BaseModel):
    status: str  # received/prepared/ready/delivered


class OnlineOrderOut(BaseModel):
    id: int
    branch_id: int
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    status: str
    pickup_slot_id: Optional[int] = None
    delivery_type: str
    total: Decimal
    created_at: datetime
    lines: List[OrderLineOut] = []

    model_config = {"from_attributes": True}
