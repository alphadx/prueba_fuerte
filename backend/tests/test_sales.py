import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_admin_and_login


_sales_counter = 0


async def _setup(client: AsyncClient, token: str):
    global _sales_counter
    _sales_counter += 1
    headers = {"Authorization": f"Bearer {token}"}
    # Company + Branch
    company_resp = await client.post(
        "/companies",
        json={"name": f"Tienda Ventas {_sales_counter}", "rut": f"76.{_sales_counter:03d}.100-1"},
        headers=headers,
    )
    company_id = company_resp.json()["id"]
    branch_resp = await client.post(
        "/branches",
        json={"company_id": company_id, "name": "Sucursal Ventas"},
        headers=headers,
    )
    branch_id = branch_resp.json()["id"]
    # Product
    prod_resp = await client.post(
        "/products",
        json={
            "name": "Pan Marraqueta",
            "sku": f"PAN{_sales_counter:03d}S",
            "branch_id": branch_id,
            "unit_price": "100.00",
            "cost_price": "60.00",
            "min_stock": "0",
        },
        headers=headers,
    )
    product_id = prod_resp.json()["id"]
    return branch_id, product_id


@pytest.mark.asyncio
async def test_cash_session_open_close(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, _ = await _setup(client, token)

    # Open session
    open_resp = await client.post(
        "/cash-sessions",
        json={"branch_id": branch_id, "opening_amount": "50000.00"},
        headers=headers,
    )
    assert open_resp.status_code == 201
    session_id = open_resp.json()["id"]
    assert open_resp.json()["status"] == "open"

    # Close session
    close_resp = await client.put(
        f"/cash-sessions/{session_id}/close",
        json={"closing_amount": "75000.00"},
        headers=headers,
    )
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"
    assert close_resp.json()["closing_amount"] == "75000.00"


@pytest.mark.asyncio
async def test_create_sale_with_payment(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    branch_id, product_id = await _setup(client, token)

    sale_resp = await client.post(
        "/sales",
        json={
            "branch_id": branch_id,
            "channel": "pos",
            "lines": [
                {
                    "product_id": product_id,
                    "quantity": "3",
                    "unit_price": "100.00",
                    "discount": "0",
                }
            ],
            "payments": [
                {"method": "cash", "amount": "300.00", "status": "confirmed"}
            ],
        },
        headers=headers,
    )
    assert sale_resp.status_code == 201
    data = sale_resp.json()
    assert float(data["total"]) == 300.00
    assert len(data["lines"]) == 1
    assert len(data["payments"]) == 1
    assert data["payments"][0]["method"] == "cash"


@pytest.mark.asyncio
async def test_list_sales(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await client.get("/sales", headers=headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
