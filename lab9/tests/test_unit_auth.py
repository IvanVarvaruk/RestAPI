import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from main import app
from uuid import uuid4

mock_user_id = uuid4()
mock_user_model = AsyncMock()
mock_user_model.id = mock_user_id
mock_user_model.username = "testuser"
mock_user_model.hashed_password = "hashed_password"

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
@patch("api.auth.UserRepository")
async def test_register_success(mock_repo_class, client):
    mock_repo = mock_repo_class.return_value
    mock_repo.get_by_username = AsyncMock(return_value=None)
    mock_repo.create = AsyncMock(return_value=mock_user_model)

    response = await client.post("/auth/register", json={"username": "testuser", "password": "password"})

    assert response.status_code == 201
    assert response.json()["username"] == "testuser"

@pytest.mark.asyncio
@patch("api.auth.UserRepository")
async def test_register_duplicate(mock_repo_class, client):
    mock_repo = mock_repo_class.return_value
    mock_repo.get_by_username = AsyncMock(return_value=mock_user_model)

    response = await client.post("/auth/register", json={"username": "testuser", "password": "password"})

    assert response.status_code == 400
    assert "Username already registered" in response.text

@pytest.mark.asyncio
@patch("api.auth.verify_password")
@patch("api.auth.UserRepository")
async def test_login_success(mock_repo_class, mock_verify, client):
    mock_repo = mock_repo_class.return_value
    mock_repo.get_by_username = AsyncMock(return_value=mock_user_model)
    mock_verify.return_value = True

    response = await client.post("/auth/login", data={"username": "testuser", "password": "password"})

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

@pytest.mark.asyncio
@patch("api.auth.UserRepository")
async def test_login_not_found(mock_repo_class, client):
    mock_repo = mock_repo_class.return_value
    mock_repo.get_by_username = AsyncMock(return_value=None)

    response = await client.post("/auth/login", data={"username": "testuser", "password": "password"})

    assert response.status_code == 401

@pytest.mark.asyncio
@patch("api.auth.verify_password")
@patch("api.auth.UserRepository")
async def test_login_invalid_password(mock_repo_class, mock_verify, client):
    mock_repo = mock_repo_class.return_value
    mock_repo.get_by_username = AsyncMock(return_value=mock_user_model)
    mock_verify.return_value = False

    response = await client.post("/auth/login", data={"username": "testuser", "password": "wrongpassword"})

    assert response.status_code == 401