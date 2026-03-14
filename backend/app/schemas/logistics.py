from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class DeliveryTaskCreate(BaseModel):
    branch_id: int
    order_id: Optional[int] = None
    employee_id: Optional[int] = None
    scheduled_date: date
    scheduled_time: str
    address: str
    parking_number: Optional[str] = None
    message: Optional[str] = None


class DeliveryTaskUpdate(BaseModel):
    employee_id: Optional[int] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    address: Optional[str] = None
    parking_number: Optional[str] = None
    message: Optional[str] = None
    status: Optional[str] = None


class DeliveryTaskOut(BaseModel):
    id: int
    branch_id: int
    order_id: Optional[int] = None
    employee_id: Optional[int] = None
    scheduled_date: date
    scheduled_time: str
    address: str
    parking_number: Optional[str] = None
    message: Optional[str] = None
    status: str
    whatsapp_link: str
    instagram_link: str
    created_at: datetime

    model_config = {"from_attributes": True}
