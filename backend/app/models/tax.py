from datetime import datetime, date, timezone
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, ForeignKey, DateTime, Date, Text, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.database import Base


def _now():
    return datetime.now(timezone.utc)


class TaxDocument(Base):
    __tablename__ = "tax_documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sale_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sales.id"), nullable=True)
    folio: Mapped[Optional[int]] = mapped_column(nullable=True)
    dte_type: Mapped[int] = mapped_column(nullable=False, default=39)  # 39=boleta
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    issuer_rut: Mapped[str] = mapped_column(String(20), nullable=False)
    receiver_rut: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    receiver_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    sii_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending/sent/accepted/rejected
    track_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    xml_signed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    sale: Mapped[Optional["app.models.sales.Sale"]] = relationship(
        "Sale", back_populates="tax_documents"
    )
    events: Mapped[List["TaxDocumentEvent"]] = relationship(
        "TaxDocumentEvent", back_populates="tax_document"
    )


class TaxDocumentEvent(Base):
    __tablename__ = "tax_document_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tax_document_id: Mapped[int] = mapped_column(
        ForeignKey("tax_documents.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sii_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    tax_document: Mapped["TaxDocument"] = relationship(
        "TaxDocument", back_populates="events"
    )
