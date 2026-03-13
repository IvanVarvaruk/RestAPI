import pytest
from httpx import AsyncClient
from main import app

@pytest.mark.asyncio
async def test_create_book():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/books/", json={
            "title": "Kobzar",
            "author": "Taras Shevchenko",
            "year": 1840,
            "status": "Available in library"
        })
    assert response.status_code == 201
    assert response.json()["title"] == "Kobzar"

@pytest.mark.asyncio
async def test_get_all_books():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/books/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_delete_book_idempotent():
    import uuid
    fake_id = str(uuid.uuid4())
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.delete(f"/books/{fake_id}")
    assert response.status_code == 204