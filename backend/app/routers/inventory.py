from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.inventory import Category, Product, StockItem, StockMovement
from app.schemas.inventory import (
    CategoryCreate, CategoryOut,
    ProductCreate, ProductUpdate, ProductOut,
    StockItemOut,
    StockMovementCreate, StockMovementOut,
)

router = APIRouter(tags=["inventory"])


# ---- Categories ----

@router.get("/categories", response_model=List[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Category))
    return result.scalars().all()


@router.post("/categories", response_model=CategoryOut, status_code=201)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = Category(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ---- Products ----

@router.get("/products", response_model=List[ProductOut])
async def list_products(
    branch_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Product)
    if branch_id is not None:
        stmt = stmt.where(Product.branch_id == branch_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/products", response_model=ProductOut, status_code=201)
async def create_product(
    payload: ProductCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = Product(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/products/{product_id}", response_model=ProductOut)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    return obj


@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(obj)


@router.get("/products/{product_id}/stock", response_model=List[StockItemOut])
async def get_product_stock(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(StockItem).where(StockItem.product_id == product_id)
    )
    return result.scalars().all()


# ---- Stock movements ----

@router.post("/stock/movements", response_model=StockMovementOut, status_code=201)
async def create_movement(
    payload: StockMovementCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Validate movement type
    allowed = {"purchase", "sale", "adjustment", "waste"}
    if payload.movement_type not in allowed:
        raise HTTPException(status_code=400, detail=f"movement_type must be one of {allowed}")

    movement = StockMovement(**payload.model_dump(), user_id=current_user.id)
    db.add(movement)

    # Update StockItem
    result = await db.execute(
        select(StockItem).where(
            and_(
                StockItem.product_id == payload.product_id,
                StockItem.branch_id == payload.branch_id,
            )
        )
    )
    stock_item = result.scalar_one_or_none()
    if stock_item is None:
        stock_item = StockItem(
            product_id=payload.product_id,
            branch_id=payload.branch_id,
            quantity=Decimal("0"),
            reserved_qty=Decimal("0"),
        )
        db.add(stock_item)

    if payload.movement_type == "purchase":
        stock_item.quantity += payload.quantity
    elif payload.movement_type in ("sale", "waste"):
        stock_item.quantity -= payload.quantity
    elif payload.movement_type == "adjustment":
        stock_item.quantity += payload.quantity  # can be negative

    await db.flush()
    await db.refresh(movement)
    return movement


@router.get("/stock/low", response_model=List[ProductOut])
async def low_stock(
    branch_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Return products where current stock < min_stock."""
    stmt = (
        select(Product)
        .join(StockItem, StockItem.product_id == Product.id)
        .where(StockItem.quantity < Product.min_stock)
    )
    if branch_id is not None:
        stmt = stmt.where(StockItem.branch_id == branch_id)
    result = await db.execute(stmt)
    return result.scalars().all()
