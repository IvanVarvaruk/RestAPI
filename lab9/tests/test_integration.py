import pytest
import pytest_asyncio
from uuid import uuid4

@pytest_asyncio.fixture
async def auth_headers(async_client):
    user_data = {"username": f"user_{uuid4()}", "password": "testpassword"}
    await async_client.post("/auth/register", json=user_data)
    login_response = await async_client.post(
        "/auth/login",
        data={"username": user_data["username"], "password": user_data["password"]}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_full_book_crud_lifecycle(async_client, auth_headers):
    new_book_data = {
        "title": "The Master and Margarita",
        "author": "Mikhail Bulgakov",
        "description": "Classic novel",
        "status": "available",
        "year": 1967
    }

    create_response = await async_client.post("/books/", json=new_book_data, headers=auth_headers)
    assert create_response.status_code == 201

    created_book = create_response.json()
    assert "id" in created_book
    assert created_book["title"] == new_book_data["title"]
    assert created_book["year"] == new_book_data["year"]

    book_id = created_book["id"]

    get_response = await async_client.get(f"/books/{book_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == book_id
    assert get_response.json()["author"] == new_book_data["author"]

    list_response = await async_client.get("/books/", headers=auth_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] >= 1
    assert any(b["id"] == book_id for b in list_data["items"])

    delete_response = await async_client.delete(f"/books/{book_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    get_deleted_response = await async_client.get(f"/books/{book_id}", headers=auth_headers)
    assert get_deleted_response.status_code == 404
    assert get_deleted_response.json()["detail"] == "Book not found"

@pytest.mark.asyncio
async def test_validation_errors(async_client, auth_headers):
    invalid_book_data = {
        "title": "Book without year",
        "author": "Unknown",
        "status": "available"
    }
    response = await async_client.post("/books/", json=invalid_book_data, headers=auth_headers)
    assert response.status_code == 422
    assert "year" in response.text

    wrong_type_data = {
        "title": "Test",
        "author": "Test",
        "status": "available",
        "year": "two thousand"
    }
    response_type = await async_client.post("/books/", json=wrong_type_data, headers=auth_headers)
    assert response_type.status_code == 422

    invalid_uuid = "12345-not-a-uuid"
    response_uuid = await async_client.get(f"/books/{invalid_uuid}", headers=auth_headers)
    assert response_uuid.status_code == 422

@pytest.mark.asyncio
async def test_offset_pagination(async_client, auth_headers):
    for i in range(5):
        await async_client.post("/books/", json={
            "title": f"Book {i}", "author": "Offset Author", "status": "read", "year": 2000 + i
        }, headers=auth_headers)

    res_page1 = await async_client.get("/books/?limit=2&offset=0&author=Offset Author", headers=auth_headers)
    assert res_page1.status_code == 200
    data1 = res_page1.json()
    assert len(data1["items"]) == 2
    assert data1["total"] == 5

    res_page2 = await async_client.get("/books/?limit=2&offset=2&author=Offset Author", headers=auth_headers)
    assert res_page2.status_code == 200
    data2 = res_page2.json()
    assert len(data2["items"]) == 2

    res_page3 = await async_client.get("/books/?limit=2&offset=4&author=Offset Author", headers=auth_headers)
    data3 = res_page3.json()
    assert len(data3["items"]) == 1

    ids_page1 = {b["id"] for b in data1["items"]}
    ids_page2 = {b["id"] for b in data2["items"]}
    assert ids_page1.isdisjoint(ids_page2)

@pytest.mark.asyncio
async def test_cursor_pagination(async_client, auth_headers):
    created_books = []
    for i in range(4):
        res = await async_client.post("/books/", json={
            "title": f"Cursor Book {i}", "author": "Cursor Author", "status": "read", "year": 2020
        }, headers=auth_headers)
        created_books.append(res.json())

    created_books.sort(key=lambda x: str(x["id"]))

    res1 = await async_client.get("/books/?limit=2&author=Cursor Author", headers=auth_headers)
    data1 = res1.json()

    assert len(data1["items"]) == 2
    assert data1["items"][0]["id"] == created_books[0]["id"]
    assert data1["items"][1]["id"] == created_books[1]["id"]

    assert data1["next_cursor"] == created_books[1]["id"]
    cursor = data1["next_cursor"]

    res2 = await async_client.get(f"/books/?limit=2&author=Cursor Author&cursor={cursor}", headers=auth_headers)
    data2 = res2.json()

    assert len(data2["items"]) == 2
    assert data2["items"][0]["id"] == created_books[2]["id"]
    assert data2["items"][1]["id"] == created_books[3]["id"]
    assert data2["next_cursor"] == created_books[3]["id"]

@pytest.mark.asyncio
async def test_filtering_and_sorting(async_client, auth_headers):
    books = [
        {"title": "Alphabet", "author": "Author A", "status": "read", "year": 2010},
        {"title": "Apple", "author": "Author B", "status": "unread", "year": 1990},
        {"title": "Primer", "author": "Author A", "status": "read", "year": 2005},
    ]
    for b in books:
        await async_client.post("/books/", json=b, headers=auth_headers)

    res_author = await async_client.get("/books/?author=Author A", headers=auth_headers)
    data_author = res_author.json()["items"]
    assert len(data_author) == 2
    assert all(b["author"] == "Author A" for b in data_author)

    res_status = await async_client.get("/books/?status=unread", headers=auth_headers)
    data_status = res_status.json()["items"]
    assert len(data_status) == 1
    assert data_status[0]["title"] == "Apple"

    res_sort_year = await async_client.get("/books/?sort_by=year", headers=auth_headers)
    data_sort_year = res_sort_year.json()["items"]
    assert len(data_sort_year) == 3
    assert data_sort_year[0]["year"] == 1990
    assert data_sort_year[1]["year"] == 2005
    assert data_sort_year[2]["year"] == 2010

    res_sort_title = await async_client.get("/books/?sort_by=title", headers=auth_headers)
    data_sort_title = res_sort_title.json()["items"]
    assert data_sort_title[0]["title"] == "Alphabet"
    assert data_sort_title[1]["title"] == "Apple"
    assert data_sort_title[2]["title"] == "Primer"