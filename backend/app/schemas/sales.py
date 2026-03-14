from datetime import datetime
from decimal import Decimal
from typing import Optional, Any, List

from pydantic import BaseModel


# ---- CashSession ----

class CashSessionCreate(BaseModel):
    branch_id: int
    opening_amount: Decimal = Decimal("0")


class CashSessionClose(BaseModel):
    closing_amount: Decimal


class CashSessionOut(BaseModel):
    id: int
    branch_id: int
    user_id: int
    opened_at: datetime
    closed_at: Optional[datetime] = None
    opening_amount: Decimal
    closing_amount: Optional[Decimal] = None
    status: str

    model_config = {"from_attributes": True}


# ---- SaleLine ----

class SaleLineCreate(BaseModel):
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal = Decimal("0")


class SaleLineOut(BaseModel):
    id: int
    sale_id: int
    product_id: int
    quantity: Decimal
    unit_price: Decimal
    discount: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


# ---- Payment ----

class PaymentCreate(BaseModel):
    method: str
    amount: Decimal
    status: str = "confirmed"
    gateway_ref: Optional[str] = None
    gateway_data: Optional[Any] = None


class PaymentOut(BaseModel):
    id: int
    sale_id: int
    method: str
    amount: Decimal
    status: str
    gateway_ref: Optional[str] = None
    gateway_data: Optional[Any] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Sale ----

class SaleCreate(BaseModel):
    branch_id: int
    cash_session_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_rut: Optional[str] = None
    channel: str = "pos"
    lines: List[SaleLineCreate]
    payments: List[PaymentCreate]


class SaleOut(BaseModel):
    id: int
    branch_id: int
    user_id: int
    cash_session_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_rut: Optional[str] = None
    total: Decimal
    tax_amount: Decimal
    net_amount: Decimal
    status: str
    channel: str
    created_at: datetime
    lines: List[SaleLineOut] = []
    payments: List[PaymentOut] = []

    model_config = {"from_attributes": True}
