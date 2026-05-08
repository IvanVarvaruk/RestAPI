import asyncio
import os
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "mongodb://localhost:27018/library4_test",
)

os.environ.setdefault("DATABASE_URL", TEST_DATABASE_URL)

from database import get_db
from main import app


pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def docker_compose_file():
    return Path(__file__).parent / "docker-compose.test.yml"


def _compose_command(compose_file):
    base = ["docker", "compose", "-f", str(compose_file)]
    try:
        subprocess.run(
            ["docker", "compose", "version"],
            check=True,
            capture_output=True,
            text=True,
        )
        return base
    except (FileNotFoundError, subprocess.CalledProcessError):
        return ["docker-compose", "-f", str(compose_file)]


async def _wait_for_database(timeout_seconds=45):
    client = AsyncIOMotorClient(TEST_DATABASE_URL, serverSelectionTimeoutMS=1000)
    deadline = time.monotonic() + timeout_seconds
    last_error = None

    while time.monotonic() < deadline:
        try:
            await client.admin.command("ping")
            client.close()
            return
        except Exception as error:
            last_error = error
            await asyncio.sleep(1)

    client.close()
    raise RuntimeError("MongoDB test container did not become ready") from last_error


@pytest.fixture(scope="session")
def test_database_container(docker_compose_file):
    command = _compose_command(docker_compose_file)
    subprocess.run([*command, "up", "-d", "test_db"], check=True)
    yield
    subprocess.run([*command, "down", "-v"], check=True)


@pytest.fixture
async def prepared_database(test_database_container):
    await _wait_for_database()
    client = AsyncIOMotorClient(TEST_DATABASE_URL)
    database = client.get_default_database()

    await database.books.drop()
    await database.books.create_index("id", unique=True)
    await database.books.create_index([("status", 1), ("author", 1)])
    await database.books.create_index([("title", 1), ("id", 1)])
    await database.books.create_index([("year", 1), ("id", 1)])

    yield database

    await database.books.drop()
    client.close()


@pytest.fixture
async def api_client(prepared_database):
    async def override_get_db():
        yield prepared_database

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def persisted_book(prepared_database, sample_book_payload):
    book = {"id": str(uuid4()), **sample_book_payload}
    await prepared_database.books.insert_one(book)
    return book


@pytest.mark.asyncio
async def test_create_and_get_book(api_client, sample_book_payload):
    create_response = await api_client.post("/books/", json=sample_book_payload)

    assert create_response.status_code == 201
    created_book = create_response.json()
    assert created_book["id"]
    assert created_book["title"] == sample_book_payload["title"]

    get_response = await api_client.get(f"/books/{created_book['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == created_book


@pytest.mark.asyncio
async def test_list_books_supports_filters_sorting_and_pagination(
    api_client,
    sample_book_payload,
):
    second_book = {
        **sample_book_payload,
        "title": "Domain-Driven Design",
        "author": "Eric Evans",
        "year": 2003,
    }
    archived_book = {
        **sample_book_payload,
        "title": "Old Notes",
        "status": "archived",
        "year": 1999,
    }

    await api_client.post("/books/", json=sample_book_payload)
    await api_client.post("/books/", json=second_book)
    await api_client.post("/books/", json=archived_book)

    response = await api_client.get(
        "/books/",
        params={
            "limit": 10,
            "offset": 0,
            "status": "available",
            "author": "e",
            "sort_by": "year",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert [book["title"] for book in body["items"]] == [
        "Domain-Driven Design",
        "Clean Architecture",
    ]
    assert body["next_cursor"] == body["items"][-1]["id"]


@pytest.mark.asyncio
async def test_delete_book_removes_it_from_database(api_client, persisted_book):
    delete_response = await api_client.delete(f"/books/{persisted_book['id']}")

    assert delete_response.status_code == 204

    get_response = await api_client.get(f"/books/{persisted_book['id']}")

    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_same_book_twice_returns_404_on_second_call(
    api_client,
    persisted_book,
):
    first_response = await api_client.delete(f"/books/{persisted_book['id']}")
    second_response = await api_client.delete(f"/books/{persisted_book['id']}")

    assert first_response.status_code == 204
    assert second_response.status_code == 404
    assert second_response.json() == {"detail": "Book not found"}


@pytest.mark.asyncio
async def test_delete_unknown_book_returns_404(api_client):
    response = await api_client.delete("/books/11111111-1111-1111-1111-111111111111")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}


@pytest.mark.asyncio
async def test_get_unknown_book_returns_404(api_client):
    response = await api_client.get("/books/11111111-1111-1111-1111-111111111111")

    assert response.status_code == 404
    assert response.json() == {"detail": "Book not found"}
