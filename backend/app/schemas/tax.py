from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Any, List

from pydantic import BaseModel


class TaxDocumentCreate(BaseModel):
    sale_id: Optional[int] = None
    dte_type: int = 39
    issue_date: date
    issuer_rut: str
    receiver_rut: Optional[str] = None
    receiver_name: Optional[str] = None
    net_amount: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")


class TaxDocumentOut(BaseModel):
    id: int
    sale_id: Optional[int] = None
    folio: Optional[int] = None
    dte_type: int
    issue_date: date
    issuer_rut: str
    receiver_rut: Optional[str] = None
    receiver_name: Optional[str] = None
    net_amount: Decimal
    tax_amount: Decimal
    total: Decimal
    sii_status: str
    track_id: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaxDocumentEventOut(BaseModel):
    id: int
    tax_document_id: int
    event_type: str
    description: Optional[str] = None
    sii_response: Optional[Any] = None
    created_at: datetime

    model_config = {"from_attributes": True}
