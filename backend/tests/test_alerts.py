from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient

from tests.conftest import create_admin_and_login
from app.models.hr import DocumentType, Employee, EmployeeDocument
from app.models.alerts import AlarmRule, AlarmEvent, Notification
from app.models.core import Role, User
from app.core.security import get_password_hash
from app.workers.alerts import run_alert_check


@pytest.mark.asyncio
async def test_alarm_rule_creation(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    # Create document type
    dt_resp = await client.post(
        "/document-types",
        json={"name": "Seguro de Vida ALR", "default_alert_days": 30},
        headers=headers,
    )
    dt_id = dt_resp.json()["id"]

    rule_resp = await client.post(
        "/alarm-rules",
        json={
            "document_type_id": dt_id,
            "days_before": 15,
            "notify_roles": ["admin", "supervisor"],
            "channel": "inapp",
        },
        headers=headers,
    )
    assert rule_resp.status_code == 201
    data = rule_resp.json()
    assert data["days_before"] == 15
    assert "admin" in data["notify_roles"]


@pytest.mark.asyncio
async def test_alert_triggering_for_expiring_documents(db: AsyncSession):
    """
    Directly test the run_alert_check worker: a document expiring soon should
    trigger an AlarmEvent.
    """
    # Setup: Role, User, DocumentType, Employee, EmployeeDocument, AlarmRule
    role = Role(name="supervisor_alert", permissions={})
    db.add(role)
    await db.flush()

    user = User(
        email="supervisor_alert@test.cl",
        hashed_password=get_password_hash("test"),
        full_name="Supervisor Alert",
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    dt = DocumentType(name="Vacuna Anual ALR", default_alert_days=30, is_active=True)
    db.add(dt)
    await db.flush()

    emp = Employee(full_name="Carlos Muñoz", rut="5.555.555-5", is_active=True)
    db.add(emp)
    await db.flush()

    # Document expiring in 5 days (within 30-day window)
    expiry = date.today() + timedelta(days=5)
    emp_doc = EmployeeDocument(
        employee_id=emp.id,
        document_type_id=dt.id,
        end_date=expiry,
        status="active",
    )
    db.add(emp_doc)
    await db.flush()

    rule = AlarmRule(
        document_type_id=dt.id,
        days_before=30,
        notify_roles=["supervisor_alert"],
        channel="inapp",
        is_active=True,
    )
    db.add(rule)
    await db.flush()
    await db.commit()

    # Run alert check
    count = await run_alert_check(db)
    assert count >= 1

    # Verify AlarmEvent was created
    result = await db.execute(
        select(AlarmEvent).where(
            AlarmEvent.alarm_rule_id == rule.id,
            AlarmEvent.employee_document_id == emp_doc.id,
        )
    )
    event = result.scalar_one_or_none()
    assert event is not None
    assert event.status == "sent"

    # Verify Notification was created for the supervisor user
    notif_result = await db.execute(
        select(Notification).where(Notification.user_id == user.id)
    )
    notif = notif_result.scalar_one_or_none()
    assert notif is not None
    assert str(emp_doc.id) in notif.link


@pytest.mark.asyncio
async def test_no_duplicate_alarm_events(db: AsyncSession):
    """Running alert check twice should not create duplicate events."""
    role = Role(name="admin_nodup", permissions={})
    db.add(role)
    await db.flush()

    dt = DocumentType(name="Examen Médico NODUP", default_alert_days=30, is_active=True)
    db.add(dt)
    await db.flush()

    emp = Employee(full_name="Luis Contreras", rut="4.444.444-4", is_active=True)
    db.add(emp)
    await db.flush()

    expiry = date.today() + timedelta(days=3)
    emp_doc = EmployeeDocument(
        employee_id=emp.id,
        document_type_id=dt.id,
        end_date=expiry,
        status="active",
    )
    db.add(emp_doc)

    rule = AlarmRule(
        document_type_id=dt.id,
        days_before=30,
        notify_roles=[],
        channel="inapp",
        is_active=True,
    )
    db.add(rule)
    await db.flush()
    await db.commit()

    count1 = await run_alert_check(db)
    count2 = await run_alert_check(db)

    assert count1 >= 1
    assert count2 == 0  # no new events on second run
