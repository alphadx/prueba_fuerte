from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, ForeignKey, DateTime, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class CashSession(Base):
    __tablename__ = "cash_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    opening_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    closing_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="open")  # open/closed

    sales: Mapped[List["Sale"]] = relationship("Sale", back_populates="cash_session")


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    cash_session_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cash_sessions.id"), nullable=True
    )
    customer_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    customer_rut: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="pos")  # pos/ecommerce
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    cash_session: Mapped[Optional["CashSession"]] = relationship(
        "CashSession", back_populates="sales"
    )
    lines: Mapped[List["SaleLine"]] = relationship("SaleLine", back_populates="sale")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="sale")
    tax_documents: Mapped[List["app.models.tax.TaxDocument"]] = relationship(
        "TaxDocument", back_populates="sale"
    )


class SaleLine(Base):
    __tablename__ = "sale_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    sale: Mapped["Sale"] = relationship("Sale", back_populates="lines")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False, index=True)
    method: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # cash/transbank/mercadopago/getnet/khipu/flow/stripe/paypal
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="confirmed"
    )  # pending/confirmed/rejected
    gateway_ref: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    gateway_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    sale: Mapped["Sale"] = relationship("Sale", back_populates="payments")
