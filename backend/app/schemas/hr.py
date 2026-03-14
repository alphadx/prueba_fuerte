from datetime import datetime, date
from typing import Optional, Any, List

from pydantic import BaseModel


# ---- Employee ----

class EmployeeBase(BaseModel):
    branch_id: Optional[int] = None
    full_name: str
    rut: str
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    is_active: bool = True


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    hire_date: Optional[date] = None
    is_active: Optional[bool] = None


class EmployeeOut(EmployeeBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- DocumentType ----

class DocumentTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    fields_schema: Optional[Any] = None
    default_alert_days: int = 30
    is_active: bool = True


class DocumentTypeCreate(DocumentTypeBase):
    pass


class DocumentTypeOut(DocumentTypeBase):
    id: int

    model_config = {"from_attributes": True}


# ---- EmployeeDocument ----

class EmployeeDocumentCreate(BaseModel):
    document_type_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "active"
    custom_data: Optional[Any] = None


class EmployeeDocumentOut(BaseModel):
    id: int
    employee_id: int
    document_type_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str
    custom_data: Optional[Any] = None
    created_at: datetime
    days_until_expiry: Optional[int] = None  # computed field

    model_config = {"from_attributes": True}


# ---- DocumentAttachment ----

class DocumentAttachmentOut(BaseModel):
    id: int
    employee_document_id: int
    filename: str
    file_path: str
    file_type: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}
