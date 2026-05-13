import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from main import app
from api.dependencies import get_current_user
from core.redis_client import get_redis
from database import get_db
from models.user import UserModel
from schemas.book import Book


async def override_get_db():
    yield AsyncMock()


def _redis_mock_with_count(count: int) -> AsyncMock:
    r = AsyncMock()
    r.zremrangebyscore = AsyncMock(return_value=0)
    r.zcard = AsyncMock(return_value=count)
    r.zadd = AsyncMock(return_value=1)
    r.expire = AsyncMock(return_value=True)
    return r


async def override_get_current_user():
    user = UserModel(username="testuser")
    user.id = uuid4()
    return user


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
@patch("api.endpoints.BookService")
async def test_rate_limit_authenticated_under_limit(mock_service_class, client):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_redis] = lambda: _redis_mock_with_count(0)

    mock_book_id = uuid4()
    mock_service = mock_service_class.return_value
    mock_service.get_book = AsyncMock(
        return_value=Book(
            id=mock_book_id,
            title="1984",
            author="George Orwell",
            description="Dystopian",
            status="available",
            year=1949,
        )
    )

    res = await client.get(f"/books/{mock_book_id}")
    assert res.status_code == 200


@pytest.mark.asyncio
@patch("api.endpoints.BookService")
async def test_rate_limit_authenticated_over_limit(mock_service_class, client):
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_redis] = lambda: _redis_mock_with_count(10)

    mock_book_id = uuid4()
    mock_service = mock_service_class.return_value
    mock_service.get_book = AsyncMock(return_value=None)

    res = await client.get(f"/books/{mock_book_id}")
    assert res.status_code == 429


@pytest.mark.asyncio
@patch("api.auth.UserRepository")
@patch("api.auth.verify_password")
async def test_rate_limit_anonymous_under_limit(mock_verify, mock_repo_class, client):
    app.dependency_overrides[get_redis] = lambda: _redis_mock_with_count(0)

    mock_user = AsyncMock()
    mock_user.username = "testuser"
    mock_user.hashed_password = "hashed_password"

    mock_repo = mock_repo_class.return_value
    mock_repo.get_by_username = AsyncMock(return_value=mock_user)
    mock_verify.return_value = True

    res = await client.post("/auth/login", data={"username": "testuser", "password": "password"})
    assert res.status_code == 200


@pytest.mark.asyncio
@patch("api.auth.UserRepository")
@patch("api.auth.verify_password")
async def test_rate_limit_anonymous_over_limit(mock_verify, mock_repo_class, client):
    app.dependency_overrides[get_redis] = lambda: _redis_mock_with_count(2)

    mock_user = AsyncMock()
    mock_user.username = "testuser"
    mock_user.hashed_password = "hashed_password"

    mock_repo = mock_repo_class.return_value
    mock_repo.get_by_username = AsyncMock(return_value=mock_user)
    mock_verify.return_value = True

    res = await client.post("/auth/login", data={"username": "testuser", "password": "password"})
    assert res.status_code == 429

