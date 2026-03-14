"""
Pytest fixtures for async SQLite in-memory tests.
"""
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.core.database import Base, get_db, init_db
from app.main import app

# SQLite in-memory URL
SQLITE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Use a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(SQLITE_URL, echo=False, connect_args={"check_same_thread": False})
    async with eng.begin() as conn:
        # Import all models so they're registered with Base
        import app.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture(scope="session")
async def session_factory(engine):
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return factory


@pytest_asyncio.fixture
async def db(session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(engine, session_factory) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with DB dependency overridden to use in-memory SQLite."""

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ---- Helper: create admin user and get token ----

async def create_admin_and_login(client: AsyncClient, db: AsyncSession) -> str:
    """
    Create a Role(admin) and a User, then login and return the JWT token.
    """
    from app.models.core import Role, User
    from app.core.security import get_password_hash

    # Create admin role if not exists
    from sqlalchemy import select
    result = await db.execute(select(Role).where(Role.name == "admin"))
    role = result.scalar_one_or_none()
    if role is None:
        role = Role(name="admin", permissions={})
        db.add(role)
        await db.flush()

    # Create user
    email = "admin@test.cl"
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            hashed_password=get_password_hash("secret"),
            full_name="Admin Test",
            role_id=role.id,
            is_active=True,
        )
        db.add(user)
        await db.flush()

    await db.commit()

    # Login
    response = await client.post(
        "/auth/login",
        data={"username": email, "password": "secret"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]
