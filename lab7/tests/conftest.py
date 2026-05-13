import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport

TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost:5433/library7_test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from main import app
from database import get_db
from models.book import Base
from models.user import UserModel
from core.redis_client import get_redis


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    TestingSessionLocal = async_sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def async_client(db_session):
    try:
        await db_session.execute(text("SELECT 1"))
    except Exception as e:
        pytest.skip(f"Test database is not reachable: {e}")

    async with db_session.bind.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(UserModel.metadata.create_all)

    async with db_session.bind.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE books CASCADE;"))
        await conn.execute(text("TRUNCATE TABLE users CASCADE;"))

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async def override_get_redis():
        from unittest.mock import AsyncMock

        r = AsyncMock()
        r.zremrangebyscore = AsyncMock(return_value=0)
        r.zcard = AsyncMock(return_value=0)
        r.zadd = AsyncMock(return_value=1)
        r.expire = AsyncMock(return_value=True)
        return r

    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
