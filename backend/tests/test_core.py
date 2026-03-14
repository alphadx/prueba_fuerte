import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_admin_and_login


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        data={"username": "nobody@test.cl", "password": "wrong"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_company(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/companies",
        json={"name": "Almacén Don Juan", "rut": "76.543.210-K", "address": "Calle 1"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Almacén Don Juan"
    assert data["rut"] == "76.543.210-K"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    # Create a role for the new user
    role_resp = await client.post(
        "/roles",
        json={"name": "cajero2", "permissions": {}},
        headers=headers,
    )
    assert role_resp.status_code == 201
    role_id = role_resp.json()["id"]

    response = await client.post(
        "/auth/register",
        json={
            "email": "cajero@test.cl",
            "password": "pass1234",
            "full_name": "Cajero Test",
            "role_id": role_id,
        },
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "cajero@test.cl"


@pytest.mark.asyncio
async def test_jwt_token_validation(client: AsyncClient, db: AsyncSession):
    token = await create_admin_and_login(client, db)
    headers = {"Authorization": f"Bearer {token}"}

    me_resp = await client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "admin@test.cl"

    # Invalid token
    bad_resp = await client.get(
        "/auth/me", headers={"Authorization": "Bearer invalidtoken"}
    )
    assert bad_resp.status_code == 401
