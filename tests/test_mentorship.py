from datetime import datetime, timedelta, timezone
import pytest
from app.jobs.expiration_worker import process_expired_requests
from app.schemas.mentorship import MentorshipStatus

@pytest.mark.asyncio
async def test_mentorship_request_lifecycle_and_deadline(async_client, student_auth, alumni_auth):
    student_headers = student_auth["headers"]
    alumni_headers = alumni_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]

    # 1. Student creates mentorship request
    req_payload = {
        "mentor_id": mentor_id,
        "message": "Hi Alex, I am a junior CS student eager to learn distributed systems and FastAPI.",
    }
    create_resp = await async_client.post("/api/v1/mentorship-requests", json=req_payload, headers=student_headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["status"] == "pending"
    assert created_data["student_id"] == student_auth["user"]["id"]
    assert created_data["mentor_id"] == mentor_id

    # Verify backend-authoritative 48-hour deadline
    created_at = datetime.fromisoformat(created_data["created_at"])
    deadline = datetime.fromisoformat(created_data["deadline"])
    diff = deadline - created_at
    assert abs(diff.total_seconds() - (48 * 3600)) < 10

    req_id = created_data["id"]

    # 2. Both participants can view it
    s_view = await async_client.get(f"/api/v1/mentorship-requests/{req_id}", headers=student_headers)
    assert s_view.status_code == 200

    m_view = await async_client.get(f"/api/v1/mentorship-requests/{req_id}", headers=alumni_headers)
    assert m_view.status_code == 200

    # 3. Unauthorized third party (valid authenticated user who is not a participant) cannot view it
    from app.repositories.user_repository import user_repo
    from app.core.security import create_access_token, hash_password
    other_user = await user_repo.create_user({
        "email": "other@test.edu",
        "hashed_password": hash_password("Password123!"),
        "role": "student",
        "name": "Other Student",
        "is_active": True,
    })
    other_token = create_access_token(subject=other_user["id"], role="student", email="other@test.edu")
    unauth_resp = await async_client.get(
        f"/api/v1/mentorship-requests/{req_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert unauth_resp.status_code == 403
    assert unauth_resp.json()["error"]["code"] == "FORBIDDEN_RESOURCE"

@pytest.mark.asyncio
async def test_cancel_mentorship_request(async_client, student_auth, alumni_auth):
    student_headers = student_auth["headers"]
    alumni_headers = alumni_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]

    create_resp = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "Mentorship request to cancel."},
        headers=student_headers,
    )
    req_id = create_resp.json()["id"]

    # Alumni cannot cancel
    alumni_cancel = await async_client.post(f"/api/v1/mentorship-requests/{req_id}/cancel", headers=alumni_headers)
    assert alumni_cancel.status_code == 403

    # Student cancels
    student_cancel = await async_client.post(f"/api/v1/mentorship-requests/{req_id}/cancel", headers=student_headers)
    assert student_cancel.status_code == 200
    assert student_cancel.json()["status"] == "cancelled"

    # Repeated cancellation rejected with 409 Conflict
    repeat_cancel = await async_client.post(f"/api/v1/mentorship-requests/{req_id}/cancel", headers=student_headers)
    assert repeat_cancel.status_code == 409

@pytest.mark.asyncio
async def test_expiration_mechanism_and_fallback(async_client, student_auth, alumni_auth):
    student_headers = student_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]

    # Create request
    create_resp = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "Test request for expiration handling."},
        headers=student_headers,
    )
    req_id = create_resp.json()["id"]

    # Simulate fast-forwarding time by 49 hours
    future_time = datetime.now(timezone.utc) + timedelta(hours=49)
    processed = await process_expired_requests(reference_time=future_time)
    assert processed >= 1

    # Check status transitioned to expired
    view_resp = await async_client.get(f"/api/v1/mentorship-requests/{req_id}", headers=student_headers)
    assert view_resp.status_code == 200
    assert view_resp.json()["status"] == "expired"

    # Verify student notification was generated
    notif_resp = await async_client.get("/api/v1/notifications", headers=student_headers)
    assert notif_resp.status_code == 200
    notifs = notif_resp.json()["items"]
    assert any(n["type"] == "request_expired" for n in notifs)
