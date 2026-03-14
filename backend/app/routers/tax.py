from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.tax import TaxDocument, TaxDocumentEvent
from app.schemas.tax import TaxDocumentCreate, TaxDocumentOut, TaxDocumentEventOut

router = APIRouter(prefix="/tax-documents", tags=["tax"])


@router.post("", response_model=TaxDocumentOut, status_code=201)
async def create_tax_document(
    payload: TaxDocumentCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = TaxDocument(**payload.model_dump(), sii_status="pending")
    db.add(obj)
    await db.flush()
    # Create initial event
    event = TaxDocumentEvent(
        tax_document_id=obj.id,
        event_type="created",
        description="Document created",
    )
    db.add(event)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/{doc_id}", response_model=TaxDocumentOut)
async def get_tax_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(TaxDocument).where(TaxDocument.id == doc_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Tax document not found")
    return obj


@router.post("/{doc_id}/query-sii", response_model=TaxDocumentOut)
async def query_sii(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """Mock endpoint: simulates querying SII status."""
    result = await db.execute(select(TaxDocument).where(TaxDocument.id == doc_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Tax document not found")
    # Mock: always returns accepted
    obj.sii_status = "accepted"
    obj.track_id = f"MOCK-{obj.id}-{datetime.now(timezone.utc).timestamp():.0f}"
    event = TaxDocumentEvent(
        tax_document_id=obj.id,
        event_type="sii_query",
        description="Mock SII query",
        sii_response={"status": "accepted", "track_id": obj.track_id},
    )
    db.add(event)
    await db.flush()
    await db.refresh(obj)
    return obj
