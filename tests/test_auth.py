import pytest

@pytest.mark.asyncio
async def test_successful_registration(async_client):
    payload = {
        "email": "newstudent@connected.edu",
        "password": "StrongPassword123!",
        "role": "student",
        "name": "Alex Student",
        "headline": "Junior CS Student",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newstudent@connected.edu"
    assert data["user"]["role"] == "student"
    # Ensure no passwords leaked
    assert "password" not in data["user"]
    assert "hashed_password" not in data["user"]

@pytest.mark.asyncio
async def test_duplicate_email_rejection(async_client, student_auth):
    payload = {
        "email": "student@connected.edu",
        "password": "Password123!",
        "role": "student",
        "name": "Another Jane",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "DUPLICATE_EMAIL"

@pytest.mark.asyncio
async def test_invalid_login(async_client, student_auth):
    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "student@connected.edu", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "INVALID_CREDENTIALS"

@pytest.mark.asyncio
async def test_auth_me_and_logout(async_client, student_auth):
    headers = student_auth["headers"]
    # Get me
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "student@connected.edu"

    # Logout
    logout_resp = await async_client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True

    # Try get me after logout -> rejected
    me_after_logout = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_after_logout.status_code == 401
    assert me_after_logout.json()["error"]["code"] == "TOKEN_REVOKED"

@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(async_client):
    response = await async_client.get("/api/v1/profiles/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
