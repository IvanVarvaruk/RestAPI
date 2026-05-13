import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_auth_flow(async_client: AsyncClient):
    user_data = {
        "username": "integrationuser",
        "password": "strongpassword123"
    }

    reg_response = await async_client.post("/auth/register", json=user_data)
    assert reg_response.status_code == 201
    assert reg_response.json()["username"] == user_data["username"]

    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    login_response = await async_client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200
    tokens = login_response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    books_response = await async_client.get("/books/", headers=headers)
    assert books_response.status_code == 200

    refresh_response = await async_client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    new_access_token = new_tokens["access_token"]

    new_headers = {"Authorization": f"Bearer {new_access_token}"}
    books_response_2 = await async_client.get("/books/", headers=new_headers)
    assert books_response_2.status_code == 200

@pytest.mark.asyncio
async def test_protected_route_without_token(async_client: AsyncClient):
    response = await async_client.get("/books/")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient):
    user_data = {
        "username": "anotheruser",
        "password": "correctpassword"
    }
    await async_client.post("/auth/register", json=user_data)

    login_data = {
        "username": user_data["username"],
        "password": "wrongpassword"
    }
    login_response = await async_client.post("/auth/login", data=login_data)
    assert login_response.status_code == 401