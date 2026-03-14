from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.alerts import AlarmRule, AlarmEvent, Notification
from app.schemas.alerts import (
    AlarmRuleCreate, AlarmRuleOut,
    AlarmEventOut,
    NotificationOut,
)

router = APIRouter(tags=["alerts"])


# ---- Alarm Rules ----

@router.get("/alarm-rules", response_model=List[AlarmRuleOut])
async def list_alarm_rules(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(AlarmRule))
    return result.scalars().all()


@router.post("/alarm-rules", response_model=AlarmRuleOut, status_code=201)
async def create_alarm_rule(
    payload: AlarmRuleCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    obj = AlarmRule(**payload.model_dump())
    db.add(obj)
    await db.flush()
    await db.refresh(obj)
    return obj


# ---- Alarm Events ----

@router.get("/alarm-events", response_model=List[AlarmEventOut])
async def list_alarm_events(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    result = await db.execute(select(AlarmEvent))
    return result.scalars().all()


@router.put("/alarm-events/{event_id}/acknowledge", response_model=AlarmEventOut)
async def acknowledge_alarm_event(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(select(AlarmEvent).where(AlarmEvent.id == event_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Alarm event not found")
    obj.acknowledged_at = datetime.now(timezone.utc)
    obj.acknowledged_by = current_user.id
    obj.status = "acknowledged"
    await db.flush()
    await db.refresh(obj)
    return obj


# ---- Notifications ----

@router.get("/notifications", response_model=List[NotificationOut])
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(Notification.user_id == current_user.id)
    )
    return result.scalars().all()


@router.put("/notifications/{notif_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notif_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notif_id,
            Notification.user_id == current_user.id,
        )
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    obj.is_read = True
    await db.flush()
    await db.refresh(obj)
    return obj
