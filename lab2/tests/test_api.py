import pytest


@pytest.mark.asyncio
async def test_create_book(client):
    response = await client.post("/book/", json={
        "title": "Clean Code",
        "author": "Robert Martin",
        "status": "Available in library",
        "year": 2008
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Clean Code"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_books_pagination(client):
    await client.post("/books/", json={
        "title": "Book 1", "author": "A", "status": "Available in library", "year": 2000
    })

    response = await client.get("/books/?limit=1&offset=0")
    assert response.status_code == 200
    json_data = response.json()
    assert len(json_data["items"]) == 1
    assert json_data["total"] >= 1


@pytest.mark.asyncio
async def test_delete_book_idempotency(client):
    res = await client.post("/books/", json={
        "title": "To Delete", "author": "A", "status": "Available in library", "year": 2000
    })
    book_id = res.json()["id"]

    res1 = await client.delete(f"/books/{book_id}")
    assert res1.status_code == 204

    res2 = await client.delete(f"/books/{book_id}")
    assert res2.status_code == 204