import pytest

@pytest.mark.asyncio
async def test_get_and_patch_my_profile(async_client, student_auth):
    headers = student_auth["headers"]
    # Get initial profile
    resp = await async_client.get("/api/v1/profiles/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "student"
    assert data["graduation_year"] == 2026

    # Patch profile: update headline and add bio, keep skills intact
    patch_payload = {
        "headline": "Aspiring Cloud Backend Architect",
        "bio": "Building scalable microservices and data pipelines.",
    }
    patch_resp = await async_client.patch("/api/v1/profiles/me", json=patch_payload, headers=headers)
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["headline"] == "Aspiring Cloud Backend Architect"
    assert updated["bio"] == "Building scalable microservices and data pipelines."
    # Preserves skills that were not submitted
    assert updated["skills"] == ["Python", "FastAPI", "React"]

@pytest.mark.asyncio
async def test_cannot_modify_protected_fields_via_profile(async_client, student_auth):
    headers = student_auth["headers"]
    # Attempt to elevate role or verify status
    payload = {
        "role": "admin",
        "verification_status": "verified",
        "headline": "Hacker",
    }
    resp = await async_client.patch("/api/v1/profiles/me", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "student"
    assert data["verification_status"] == "unverified"

@pytest.mark.asyncio
async def test_view_alumni_and_verification(async_client, student_auth, alumni_auth):
    headers = student_auth["headers"]
    alumni_id = alumni_auth["user"]["id"]

    # View alumni profile
    resp = await async_client.get(f"/api/v1/alumni/{alumni_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == alumni_id
    assert data["current_organization"] == "Google"
    assert "FastAPI" in data["skills"]

    # View alumni verification
    ver_resp = await async_client.get(f"/api/v1/alumni/{alumni_id}/verification", headers=headers)
    assert ver_resp.status_code == 200
    ver_data = ver_resp.json()
    assert ver_data["verification_status"] == "verified"
    assert ver_data["freshness_score"] >= 0.0

@pytest.mark.asyncio
async def test_private_profile_visibility(async_client, student_auth, alumni_auth):
    # Set alumni profile to private
    from app.repositories.profile_repository import profile_repo
    await profile_repo.collection.update_one(
        {"user_id": alumni_auth["user"]["id"]},
        {"$set": {"visibility": "private"}},
    )

    # Student viewing private alumni profile -> rejected 404
    resp = await async_client.get(f"/api/v1/alumni/{alumni_auth['user']['id']}", headers=student_auth["headers"])
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PROFILE_NOT_VISIBLE"

    # Alumni viewing own profile -> allowed 200
    own_resp = await async_client.get(f"/api/v1/alumni/{alumni_auth['user']['id']}", headers=alumni_auth["headers"])
    assert own_resp.status_code == 200
