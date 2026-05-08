from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from schemas.book import BookCreate
from services import book_service
from services.book_service import BookService


@pytest.fixture
def mocked_repository(monkeypatch):
    repository = AsyncMock()
    monkeypatch.setattr(book_service, "BookRepository", lambda db: repository)
    return repository


@pytest.fixture
def service(mocked_repository):
    return BookService(db=object())


@pytest.mark.asyncio
async def test_list_books_delegates_filters_to_repository(service, mocked_repository):
    cursor = uuid4()
    expected_books = [object()]
    mocked_repository.get_all.return_value = (1, expected_books)

    result = await service.list_books(
        limit=5,
        offset=10,
        status="available",
        author="Martin",
        sort_by="year",
        cursor=cursor,
    )

    assert result == (1, expected_books)
    mocked_repository.get_all.assert_awaited_once_with(
        5,
        10,
        "available",
        "Martin",
        "year",
        cursor,
    )


@pytest.mark.asyncio
async def test_create_book_delegates_payload_to_repository(
    service,
    mocked_repository,
    sample_book_payload,
):
    book_payload = BookCreate(**sample_book_payload)
    created_book = object()
    mocked_repository.create.return_value = created_book

    result = await service.create_book(book_payload)

    assert result is created_book
    mocked_repository.create.assert_awaited_once_with(book_payload)


@pytest.mark.asyncio
async def test_get_book_delegates_id_to_repository(service, mocked_repository):
    book_id = uuid4()
    expected_book = object()
    mocked_repository.get_by_id.return_value = expected_book

    result = await service.get_book(book_id)

    assert result is expected_book
    mocked_repository.get_by_id.assert_awaited_once_with(book_id)


@pytest.mark.asyncio
async def test_delete_book_delegates_id_to_repository(service, mocked_repository):
    book_id = uuid4()
    mocked_repository.delete.return_value = True

    result = await service.delete_book(book_id)

    assert result is True
    mocked_repository.delete.assert_awaited_once_with(book_id)
