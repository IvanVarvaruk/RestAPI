from types import SimpleNamespace
from unittest.mock import Mock
from uuid import UUID

import pytest
import uuid6

from main import create_app


@pytest.fixture
def service():
    return Mock()


@pytest.fixture
def client(service):
    app = create_app({"TESTING": True, "INIT_DB": False, "BOOK_SERVICE_PROVIDER": lambda: service})
    with app.test_client() as test_client:
        yield test_client


def book_object(book_id=None, title="1984", author="George Orwell", description="Dystopian", status="available", year=1949):
    return SimpleNamespace(
        id=book_id or uuid6.uuid7(),
        title=title,
        author=author,
        description=description,
        status=status,
        year=year,
    )


def test_get_book_success(client, service):
    book_id = uuid6.uuid7()
    service.get_book.return_value = book_object(book_id=book_id)

    response = client.get(f"/books/{book_id}")

    assert response.status_code == 200
    assert response.json["title"] == "1984"
    service.get_book.assert_called_once_with(book_id)


def test_get_book_not_found(client, service):
    book_id = uuid6.uuid7()
    service.get_book.return_value = None

    response = client.get(f"/books/{book_id}")

    assert response.status_code == 404
    assert response.json["detail"] == "Book not found"


def test_create_book_success(client, service):
    book_id = uuid6.uuid7()
    service.create_book.return_value = book_object(book_id=book_id)
    payload = {
        "title": "1984",
        "author": "George Orwell",
        "status": "available",
        "year": 1949,
    }

    response = client.post("/books/", json=payload)

    assert response.status_code == 201
    assert response.json["id"] == str(book_id)
    assert response.json["title"] == payload["title"]
    service.create_book.assert_called_once_with({**payload, "description": None})


def test_create_book_validation_error(client, service):
    response = client.post("/books/", json={"title": "1984", "author": "George Orwell", "status": "available"})

    assert response.status_code == 422
    assert "year" in response.text
    service.create_book.assert_not_called()


def test_list_books_uses_query_parameters(client, service):
    first = book_object(title="A", author="Author", year=2001)
    second = book_object(title="B", author="Author", year=2002)
    service.list_books.return_value = (2, [first, second])

    response = client.get(f"/books/?limit=2&offset=1&author=Author&status=read&sort_by=year&cursor={first.id}")

    assert response.status_code == 200
    assert response.json["total"] == 2
    assert response.json["next_cursor"] == str(second.id)
    service.list_books.assert_called_once_with(2, 1, "read", "Author", "year", UUID(str(first.id)))


def test_delete_book_success(client, service):
    book_id = uuid6.uuid7()
    service.delete_book.return_value = True

    response = client.delete(f"/books/{book_id}")

    assert response.status_code == 204
    service.delete_book.assert_called_once_with(book_id)
