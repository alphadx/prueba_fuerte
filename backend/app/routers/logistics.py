from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.logistics import DeliveryTask
from app.schemas.logistics import DeliveryTaskCreate, DeliveryTaskUpdate, DeliveryTaskOut

router = APIRouter(prefix="/delivery-tasks", tags=["logistics"])


@router.get("", response_model=List[DeliveryTaskOut])
async def list_delivery_tasks(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(DeliveryTask))
    return result.scalars().all()


@router.post("", response_model=DeliveryTaskOut, status_code=201)
async def create_delivery_task(
    payload: DeliveryTaskCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = DeliveryTask(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/{task_id}", response_model=DeliveryTaskOut)
async def get_delivery_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(DeliveryTask).where(DeliveryTask.id == task_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Delivery task not found")
    return obj


@router.put("/{task_id}", response_model=DeliveryTaskOut)
async def update_delivery_task(
    task_id: int,
    payload: DeliveryTaskUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(DeliveryTask).where(DeliveryTask.id == task_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Delivery task not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    await db.flush()
    await db.refresh(obj)
    return obj


@router.get("/{task_id}/share/whatsapp")
async def share_whatsapp(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(DeliveryTask).where(DeliveryTask.id == task_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Delivery task not found")
    return {"url": obj.whatsapp_link}


@router.get("/{task_id}/share/instagram")
async def share_instagram(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    result = await db.execute(select(DeliveryTask).where(DeliveryTask.id == task_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Delivery task not found")
    return {"url": obj.instagram_link}
