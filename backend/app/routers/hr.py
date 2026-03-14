from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.hr import Employee, DocumentType, EmployeeDocument, DocumentAttachment
from app.schemas.hr import (
    EmployeeCreate, EmployeeUpdate, EmployeeOut,
    DocumentTypeCreate, DocumentTypeOut,
    EmployeeDocumentCreate, EmployeeDocumentOut,
    DocumentAttachmentOut,
)

router = APIRouter(tags=["hr"])


def _days_until_expiry(end_date: Optional[date]) -> Optional[int]:
    if end_date is None:
        return None
    return (end_date - date.today()).days


def _doc_to_out(doc: EmployeeDocument) -> EmployeeDocumentOut:
    data = EmployeeDocumentOut.model_validate(doc)
    data.days_until_expiry = _days_until_expiry(doc.end_date)
    return data


# ---- Employees ----

@router.get("/employees", response_model=List[EmployeeOut])
async def list_employees(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(Employee))
    return result.scalars().all()


@router.post("/employees", response_model=EmployeeOut, status_code=201)
async def create_employee(
    payload: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = Employee(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
async def get_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Employee not found")
    return obj


@router.put("/employees/{employee_id}", response_model=EmployeeOut)
async def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Employee not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.delete("/employees/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Employee not found")
    await db.delete(obj)


# ---- Document Types ----

@router.get("/document-types", response_model=List[DocumentTypeOut])
async def list_document_types(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(DocumentType))
    return result.scalars().all()


@router.post("/document-types", response_model=DocumentTypeOut, status_code=201)
async def create_document_type(
    payload: DocumentTypeCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = DocumentType(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ---- Employee Documents ----

@router.post("/employees/{employee_id}/documents", response_model=EmployeeDocumentOut, status_code=201)
async def create_employee_document(
    employee_id: int,
    payload: EmployeeDocumentCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    # Verify employee exists
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Employee not found")

    obj = EmployeeDocument(employee_id=employee_id, **payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return _doc_to_out(obj)


@router.get("/employees/{employee_id}/documents", response_model=List[EmployeeDocumentOut])
async def list_employee_documents(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(
        select(EmployeeDocument).where(EmployeeDocument.employee_id == employee_id)
    )
    docs = result.scalars().all()
    return [_doc_to_out(d) for d in docs]


@router.get("/documents/expiring", response_model=List[EmployeeDocumentOut])
async def expiring_documents(
    days: int = Query(30, description="Documents expiring within N days"),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    today = date.today()
    threshold = today + timedelta(days=days)
    result = await db.execute(
        select(EmployeeDocument).where(
            and_(
                EmployeeDocument.end_date.isnot(None),
                EmployeeDocument.end_date <= threshold,
                EmployeeDocument.end_date >= today,
                EmployeeDocument.status == "active",
            )
        )
    )
    docs = result.scalars().all()
    return [_doc_to_out(d) for d in docs]
