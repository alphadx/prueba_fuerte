from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, ForeignKey, DateTime, Date, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Numeric

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class PickupSlot(Base):
    __tablename__ = "pickup_slots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)  # HH:MM
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    max_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    current_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    orders: Mapped[List["OnlineOrder"]] = relationship(
        "OnlineOrder", back_populates="pickup_slot"
    )


class OnlineOrder(Base):
    __tablename__ = "online_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False, index=True)
    customer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    customer_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="received"
    )  # received/prepared/ready/delivered
    pickup_slot_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("pickup_slots.id"), nullable=True
    )
    delivery_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pickup"
    )  # pickup/delivery
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    pickup_slot: Mapped[Optional["PickupSlot"]] = relationship(
        "PickupSlot", back_populates="orders"
    )
    lines: Mapped[List["OrderLine"]] = relationship("OrderLine", back_populates="order")


class OrderLine(Base):
    __tablename__ = "order_lines"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("online_orders.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["OnlineOrder"] = relationship("OnlineOrder", back_populates="lines")
