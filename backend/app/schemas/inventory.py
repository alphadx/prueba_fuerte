from datetime import datetime
from decimal import Decimal
from typing import Optional, Any, List

from pydantic import BaseModel


# ---- Category ----

class CategoryBase(BaseModel):
    name: str
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryOut(CategoryBase):
    id: int

    model_config = {"from_attributes": True}


# ---- Product ----

class ProductBase(BaseModel):
    branch_id: Optional[int] = None
    category_id: Optional[int] = None
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    unit_price: Decimal = Decimal("0")
    cost_price: Decimal = Decimal("0")
    min_stock: Decimal = Decimal("0")
    is_active: bool = True
    variants: Optional[Any] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    min_stock: Optional[Decimal] = None
    is_active: Optional[bool] = None
    variants: Optional[Any] = None
    category_id: Optional[int] = None


class ProductOut(ProductBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- StockItem ----

class StockItemOut(BaseModel):
    id: int
    product_id: int
    branch_id: int
    quantity: Decimal
    reserved_qty: Decimal
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- StockMovement ----

class StockMovementCreate(BaseModel):
    product_id: int
    branch_id: int
    movement_type: str  # purchase/sale/adjustment/waste
    quantity: Decimal
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None


class StockMovementOut(StockMovementCreate):
    id: int
    created_at: datetime
    user_id: Optional[int] = None

    model_config = {"from_attributes": True}
