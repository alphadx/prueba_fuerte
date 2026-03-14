from datetime import datetime, date, timezone
from typing import Optional, List

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Date, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    branch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("branches.id"), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    rut: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hire_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    documents: Mapped[List["EmployeeDocument"]] = relationship(
        "EmployeeDocument", back_populates="employee"
    )


class DocumentType(Base):
    __tablename__ = "document_types"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fields_schema: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    default_alert_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    employee_documents: Mapped[List["EmployeeDocument"]] = relationship(
        "EmployeeDocument", back_populates="document_type"
    )
    alarm_rules: Mapped[List["app.models.alerts.AlarmRule"]] = relationship(
        "AlarmRule", back_populates="document_type"
    )


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    document_type_id: Mapped[int] = mapped_column(
        ForeignKey("document_types.id"), nullable=False
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active/expired/revoked
    custom_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="documents")
    document_type: Mapped["DocumentType"] = relationship(
        "DocumentType", back_populates="employee_documents"
    )
    attachments: Mapped[List["DocumentAttachment"]] = relationship(
        "DocumentAttachment", back_populates="employee_document"
    )
    alarm_events: Mapped[List["app.models.alerts.AlarmEvent"]] = relationship(
        "AlarmEvent", back_populates="employee_document"
    )


class DocumentAttachment(Base):
    __tablename__ = "document_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_document_id: Mapped[int] = mapped_column(
        ForeignKey("employee_documents.id"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    employee_document: Mapped["EmployeeDocument"] = relationship(
        "EmployeeDocument", back_populates="attachments"
    )
