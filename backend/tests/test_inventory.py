import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_admin_and_login


_inv_counter = 0


async def _get_branch_id(client: AsyncClient, token: str, db: AsyncSession) -> int:
    """Create a company + branch and return branch_id."""
    global _inv_counter
    _inv_counter += 1
    headers = {"Authorization": f"Bearer {token}"}

    company_resp = await client.post(
        "/companies",
        json={"name": f"Tienda Inventario {_inv_counter}", "rut": f"77.{_inv_counter:03d}.001-1"},
        headers=headers,
    )
    company_id = company_resp.json()["id"]

    branch_resp = await client.post(
        "/branches",
        json={"company_id": company_id, "name": "Sucursal Central"},
        headers=headers,
    )
    return branch_resp.json()["id"]


@pytest.mark.asyncio
async def test_product_crud(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    branch_id = await _get_branch_id(client, token, db)

    # Create
    resp = await client.post(
        "/products",
        json={
            "name": "Arroz 1kg",
            "sku": f"ARR{_inv_counter:03d}",
            "branch_id": branch_id,
            "unit_price": "1500.00",
            "cost_price": "1200.00",
            "min_stock": "10",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    product_id = resp.json()["id"]
    created_sku = resp.json()["sku"]

    # Read
    get_resp = await client.get(f"/products/{product_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["sku"] == created_sku

    # Update
    put_resp = await client.put(
        f"/products/{product_id}",
        json={"unit_price": "1600.00"},
        headers=headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["unit_price"] == "1600.00"

    # Delete
    del_resp = await client.delete(f"/products/{product_id}", headers=headers)
    assert del_resp.status_code == 204


@pytest.mark.asyncio
async def test_stock_movement_purchase_adds_stock(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    branch_id = await _get_branch_id(client, token, db)

    # Create product
    prod_resp = await client.post(
        "/products",
        json={
            "name": "Azúcar 1kg",
            "sku": f"AZU{_inv_counter:03d}",
            "branch_id": branch_id,
            "unit_price": "900.00",
            "cost_price": "700.00",
            "min_stock": "5",
        },
        headers=headers,
    )
    product_id = prod_resp.json()["id"]

    # Purchase movement
    mov_resp = await client.post(
        "/stock/movements",
        json={
            "product_id": product_id,
            "branch_id": branch_id,
            "movement_type": "purchase",
            "quantity": "20",
        },
        headers=headers,
    )
    assert mov_resp.status_code == 201

    # Check stock
    stock_resp = await client.get(f"/products/{product_id}/stock", headers=headers)
    assert stock_resp.status_code == 200
    items = stock_resp.json()
    assert len(items) == 1
    assert float(items[0]["quantity"]) == 20.0


@pytest.mark.asyncio
async def test_stock_movement_sale_reduces_stock(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    branch_id = await _get_branch_id(client, token, db)

    prod_resp = await client.post(
        "/products",
        json={
            "name": "Aceite 1L",
            "sku": f"ACE{_inv_counter:03d}",
            "branch_id": branch_id,
            "unit_price": "2500.00",
            "cost_price": "2000.00",
            "min_stock": "3",
        },
        headers=headers,
    )
    product_id = prod_resp.json()["id"]

    # Add stock first
    await client.post(
        "/stock/movements",
        json={"product_id": product_id, "branch_id": branch_id, "movement_type": "purchase", "quantity": "10"},
        headers=headers,
    )

    # Sale reduces
    await client.post(
        "/stock/movements",
        json={"product_id": product_id, "branch_id": branch_id, "movement_type": "sale", "quantity": "4"},
        headers=headers,
    )

    stock_resp = await client.get(f"/products/{product_id}/stock", headers=headers)
    items = stock_resp.json()
    assert float(items[0]["quantity"]) == 6.0


@pytest.mark.asyncio
async def test_low_stock_alert(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}
    branch_id = await _get_branch_id(client, token, db)

    expected_sku = f"SAL{_inv_counter:03d}"

    # Product with min_stock=10, we'll only add 2
    prod_resp = await client.post(
        "/products",
        json={
            "name": "Sal 1kg",
            "sku": expected_sku,
            "branch_id": branch_id,
            "unit_price": "500.00",
            "cost_price": "300.00",
            "min_stock": "10",
        },
        headers=headers,
    )
    product_id = prod_resp.json()["id"]

    await client.post(
        "/stock/movements",
        json={"product_id": product_id, "branch_id": branch_id, "movement_type": "purchase", "quantity": "2"},
        headers=headers,
    )

    low_resp = await client.get(f"/stock/low?branch_id={branch_id}", headers=headers)
    assert low_resp.status_code == 200
    skus = [p["sku"] for p in low_resp.json()]
    assert expected_sku in skus
