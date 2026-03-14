from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.sales import CashSession, Sale, SaleLine, Payment
from app.schemas.sales import (
    CashSessionCreate, CashSessionClose, CashSessionOut,
    SaleCreate, SaleOut,
)

router = APIRouter(tags=["sales"])

TAX_RATE = Decimal("0.19")  # 19% IVA Chile


# ---- Cash Sessions ----

@router.post("/cash-sessions", response_model=CashSessionOut, status_code=201)
async def open_cash_session(
    payload: CashSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    session = CashSession(
        branch_id=payload.branch_id,
        user_id=current_user.id,
        opening_amount=payload.opening_amount,
        status="open",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


@router.put("/cash-sessions/{session_id}/close", response_model=CashSessionOut)
async def close_cash_session(
    session_id: int,
    payload: CashSessionClose,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(CashSession).where(CashSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Cash session not found")
    if session.status == "closed":
        raise HTTPException(status_code=400, detail="Session already closed")
    session.closed_at = datetime.now(timezone.utc)
    session.closing_amount = payload.closing_amount
    session.status = "closed"
    await db.flush()
    await db.refresh(session)
    return session


@router.get("/cash-sessions/{session_id}", response_model=CashSessionOut)
async def get_cash_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(CashSession).where(CashSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Cash session not found")
    return session


# ---- Sales ----

@router.post("/sales", response_model=SaleOut, status_code=201)
async def create_sale(
    payload: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    total = sum(
        (line.unit_price * line.quantity - line.discount) for line in payload.lines
    )
    net_amount = (total / (1 + TAX_RATE)).quantize(Decimal("0.01"))
    tax_amount = (total - net_amount).quantize(Decimal("0.01"))

    sale = Sale(
        branch_id=payload.branch_id,
        user_id=current_user.id,
        cash_session_id=payload.cash_session_id,
        customer_name=payload.customer_name,
        customer_rut=payload.customer_rut,
        total=total,
        tax_amount=tax_amount,
        net_amount=net_amount,
        channel=payload.channel,
        status="completed",
    )
    db.add(sale)
    await db.flush()

    for line_data in payload.lines:
        subtotal = (line_data.unit_price * line_data.quantity - line_data.discount).quantize(
            Decimal("0.01")
        )
        line = SaleLine(
            sale_id=sale.id,
            product_id=line_data.product_id,
            quantity=line_data.quantity,
            unit_price=line_data.unit_price,
            discount=line_data.discount,
            subtotal=subtotal,
        )
        db.add(line)

    for pay_data in payload.payments:
        payment = Payment(
            sale_id=sale.id,
            method=pay_data.method,
            amount=pay_data.amount,
            status=pay_data.status,
            gateway_ref=pay_data.gateway_ref,
            gateway_data=pay_data.gateway_data,
        )
        db.add(payment)

    await db.flush()

    result = await db.execute(
        select(Sale)
        .options(selectinload(Sale.lines), selectinload(Sale.payments))
        .where(Sale.id == sale.id)
    )
    return result.scalar_one()


@router.get("/sales", response_model=List[SaleOut])
async def list_sales(
    branch_id: Optional[int] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    method: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    stmt = select(Sale).options(selectinload(Sale.lines), selectinload(Sale.payments))
    if branch_id:
        stmt = stmt.where(Sale.branch_id == branch_id)
    if from_date:
        stmt = stmt.where(Sale.created_at >= from_date)
    if to_date:
        stmt = stmt.where(Sale.created_at <= to_date)
    if method:
        stmt = stmt.join(Payment).where(Payment.method == method)
    result = await db.execute(stmt)
    return result.scalars().unique().all()


@router.get("/sales/{sale_id}", response_model=SaleOut)
async def get_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(Sale)
        .options(selectinload(Sale.lines), selectinload(Sale.payments))
        .where(Sale.id == sale_id)
    )
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return sale
