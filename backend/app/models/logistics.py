from datetime import datetime, date, timezone
from typing import Optional
from urllib.parse import quote

from sqlalchemy import String, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class DeliveryTask(Base):
    __tablename__ = "delivery_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False, index=True)
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("online_orders.id"), nullable=True
    )
    employee_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employees.id"), nullable=True
    )
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[str] = mapped_column(String(10), nullable=False)  # HH:MM
    address: Mapped[str] = mapped_column(Text, nullable=False)
    parking_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending/in_transit/delivered/failed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    @property
    def whatsapp_link(self) -> str:
        text = (
            f"Entrega programada: {self.address} "
            f"el {self.scheduled_date} a las {self.scheduled_time}."
        )
        if self.parking_number:
            text += f" Estacionamiento: {self.parking_number}."
        if self.message:
            text += f" {self.message}"
        return f"https://wa.me/?text={quote(text)}"

    @property
    def instagram_link(self) -> str:
        return "https://www.instagram.com/"
