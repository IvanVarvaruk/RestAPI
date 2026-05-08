import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from main import app
from schemas.book import Book

mock_book_id = uuid4()
mock_book_data = {
    "id": str(mock_book_id),
    "title": "1984",
    "author": "George Orwell",
    "description": "Dystopian",
    "status": "available",
    "year": 1949
}


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
@patch("api.endpoints.BookService")
async def test_get_book_success(mock_service_class, client):
    mock_service = mock_service_class.return_value
    mock_service.get_book = AsyncMock(return_value=Book(**mock_book_data))

    response = await client.get(f"/books/{mock_book_id}")

    assert response.status_code == 200
    assert response.json()["title"] == "1984"
    mock_service.get_book.assert_called_once_with(mock_book_id)


@pytest.mark.asyncio
@patch("api.endpoints.BookService")
async def test_get_book_not_found(mock_service_class, client):
    mock_service = mock_service_class.return_value
    mock_service.get_book = AsyncMock(return_value=None)

    response = await client.get(f"/books/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Book not found"


@pytest.mark.asyncio
@patch("api.endpoints.BookService")
async def test_create_book_success(mock_service_class, client):
    mock_service = mock_service_class.return_value
    mock_service.create_book = AsyncMock(return_value=Book(**mock_book_data))

    payload = {
        "title": "1984",
        "author": "George Orwell",
        "status": "available",
        "year": 1949
    }

    response = await client.post("/books/", json=payload)

    assert response.status_code == 201
    assert response.json()["title"] == payload["title"]
    mock_service.create_book.assert_called_once()


@pytest.mark.asyncio
async def test_create_book_validation_error(client):
    payload = {
        "title": "1984",
        "author": "George Orwell",
        "status": "available"
    }

    response = await client.post("/books/", json=payload)

    assert response.status_code == 422
    assert "year" in response.text