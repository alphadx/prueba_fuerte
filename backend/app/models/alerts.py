from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class AlarmRule(Base):
    __tablename__ = "alarm_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    document_type_id: Mapped[int] = mapped_column(
        ForeignKey("document_types.id"), nullable=False, index=True
    )
    days_before: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    notify_roles: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False, default="inapp"
    )  # inapp/email/whatsapp
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    document_type: Mapped["app.models.hr.DocumentType"] = relationship(
        "DocumentType", back_populates="alarm_rules"
    )
    events: Mapped[List["AlarmEvent"]] = relationship("AlarmEvent", back_populates="alarm_rule")


class AlarmEvent(Base):
    __tablename__ = "alarm_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    alarm_rule_id: Mapped[int] = mapped_column(
        ForeignKey("alarm_rules.id"), nullable=False, index=True
    )
    employee_document_id: Mapped[int] = mapped_column(
        ForeignKey("employee_documents.id"), nullable=False, index=True
    )
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    acknowledged_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending/sent/acknowledged

    alarm_rule: Mapped["AlarmRule"] = relationship("AlarmRule", back_populates="events")
    employee_document: Mapped["app.models.hr.EmployeeDocument"] = relationship(
        "EmployeeDocument", back_populates="alarm_events"
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped["app.models.core.User"] = relationship(
        "User",
        back_populates="notifications",
        foreign_keys=[user_id],
    )
