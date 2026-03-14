from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_admin_and_login


@pytest.mark.asyncio
async def test_employee_creation(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/employees",
        json={
            "full_name": "Juan Pérez",
            "rut": "12.345.678-9",
            "email": "juan@almacen.cl",
            "position": "Cajero",
            "hire_date": "2023-01-15",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["full_name"] == "Juan Pérez"
    assert data["rut"] == "12.345.678-9"


@pytest.mark.asyncio
async def test_document_type_with_custom_fields(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.post(
        "/document-types",
        json={
            "name": "Licencia de Conducir HR",
            "description": "Licencia vehicular",
            "fields_schema": [
                {
                    "name": "license_type",
                    "type": "select",
                    "options": ["A", "B", "C"],
                    "required": True,
                }
            ],
            "default_alert_days": 30,
        },
        headers=headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Licencia de Conducir HR"
    assert len(data["fields_schema"]) == 1
    assert data["fields_schema"][0]["name"] == "license_type"


@pytest.mark.asyncio
async def test_employee_document_with_custom_data(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    # Create employee
    emp_resp = await client.post(
        "/employees",
        json={"full_name": "María González", "rut": "9.876.543-2", "position": "Supervisora"},
        headers=headers,
    )
    emp_id = emp_resp.json()["id"]

    # Create doc type
    dt_resp = await client.post(
        "/document-types",
        json={"name": "Contrato Indefinido HR2", "default_alert_days": 60},
        headers=headers,
    )
    dt_id = dt_resp.json()["id"]

    # Attach document with custom data
    future_date = (date.today() + timedelta(days=365)).isoformat()
    doc_resp = await client.post(
        f"/employees/{emp_id}/documents",
        json={
            "document_type_id": dt_id,
            "start_date": date.today().isoformat(),
            "end_date": future_date,
            "custom_data": {"notes": "Renovación anual"},
        },
        headers=headers,
    )
    assert doc_resp.status_code == 201
    data = doc_resp.json()
    assert data["custom_data"]["notes"] == "Renovación anual"
    assert data["days_until_expiry"] is not None
    assert data["days_until_expiry"] > 0


@pytest.mark.asyncio
async def test_expiry_detection(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    emp_resp = await client.post(
        "/employees",
        json={"full_name": "Pedro Rojas", "rut": "11.222.333-4", "position": "Bodeguero"},
        headers=headers,
    )
    emp_id = emp_resp.json()["id"]

    dt_resp = await client.post(
        "/document-types",
        json={"name": "Certificado Salud HR3", "default_alert_days": 30},
        headers=headers,
    )
    dt_id = dt_resp.json()["id"]

    # Document expiring in 10 days (within 30-day window)
    expiry = (date.today() + timedelta(days=10)).isoformat()
    await client.post(
        f"/employees/{emp_id}/documents",
        json={
            "document_type_id": dt_id,
            "end_date": expiry,
            "status": "active",
        },
        headers=headers,
    )

    # Should appear in expiring endpoint with days=30
    expiring_resp = await client.get("/documents/expiring?days=30", headers=headers)
    assert expiring_resp.status_code == 200
    items = expiring_resp.json()
    emp_doc_ids = [i["employee_id"] for i in items]
    assert emp_id in emp_doc_ids
