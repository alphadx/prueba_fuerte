from datetime import datetime
from typing import Optional, Any, List

from pydantic import BaseModel


# ---- AlarmRule ----

class AlarmRuleCreate(BaseModel):
    document_type_id: int
    days_before: int = 30
    notify_roles: Optional[Any] = None
    channel: str = "inapp"
    is_active: bool = True


class AlarmRuleOut(BaseModel):
    id: int
    document_type_id: int
    days_before: int
    notify_roles: Optional[Any] = None
    channel: str
    is_active: bool

    model_config = {"from_attributes": True}


# ---- AlarmEvent ----

class AlarmEventOut(BaseModel):
    id: int
    alarm_rule_id: int
    employee_document_id: int
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    status: str

    model_config = {"from_attributes": True}


# ---- Notification ----

class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    body: Optional[str] = None
    link: Optional[str] = None
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
