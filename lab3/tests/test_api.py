import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

MOCK_UUID = str(uuid4())

SERVICE_MOCK_PATH = "api.endpoints.BookService"


@pytest.mark.asyncio
@patch(SERVICE_MOCK_PATH)
async def test_create_book(mock_book_service_class, client):
    mock_service = AsyncMock()
    mock_book_service_class.return_value = mock_service

    mock_service.create_book.return_value = {
        "id": MOCK_UUID,
        "title": "Clean Code",
        "author": "Robert Martin",
        "description": "Programming book",
        "status": "Available",
        "year": 2008
    }

    response = await client.post("/books/", json={
        "title": "Clean Code",
        "author": "Robert Martin",
        "status": "Available",
        "year": 2008
    })

    assert response.status_code == 201
    assert response.json()["title"] == "Clean Code"
    assert response.json()["id"] == MOCK_UUID
    mock_service.create_book.assert_called_once()


@pytest.mark.asyncio
@patch(SERVICE_MOCK_PATH)
async def test_get_books_pagination_and_cursor(mock_book_service_class, client):
    mock_service = AsyncMock()
    mock_book_service_class.return_value = mock_service

    mock_book = AsyncMock()
    mock_book.id = MOCK_UUID
    mock_book.title = "Book 1"
    mock_book.author = "Author A"
    mock_book.description = "Some description"
    mock_book.status = "Available"
    mock_book.year = 2000

    mock_service.list_books.return_value = (100, [mock_book])

    response = await client.get("/books/?limit=1&offset=0")

    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data["items"]) == 1
    assert json_data["total"] == 100
    mock_service.list_books.assert_called_once()


@pytest.mark.asyncio
@patch(SERVICE_MOCK_PATH)
async def test_delete_book(mock_book_service_class, client):
    mock_service = AsyncMock()
    mock_book_service_class.return_value = mock_service

    mock_service.delete_book.return_value = None

    response = await client.delete(f"/books/{MOCK_UUID}")

    assert response.status_code == 204
    mock_service.delete_book.assert_called_once()