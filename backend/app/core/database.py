from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Engine is created lazily per-app; overridden in tests
_engine = None
_async_session_factory = None


def init_db(database_url: str) -> None:
    global _engine, _async_session_factory
    _engine = create_async_engine(database_url, echo=False, future=True)
    _async_session_factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )


async def get_db():
    if _async_session_factory is None:
        from app.core.config import settings
        init_db(settings.DATABASE_URL)
    async with _async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_all_tables(engine=None):
    from app.models import _all_models  # noqa: F401 – ensure models are registered
    target = engine or _engine
    async with target.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables(engine=None):
    from app.models import _all_models  # noqa: F401
    target = engine or _engine
    async with target.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
