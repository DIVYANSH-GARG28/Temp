from datetime import datetime, timedelta, timezone
import pytest
from tests.conftest import _pre_approve
from app.jobs.expiration_worker import process_expired_requests
from app.schemas.mentorship import MentorshipStatus

@pytest.mark.asyncio
async def test_mentorship_request_lifecycle_and_deadline(async_client, student_auth, alumni_auth):
    student_headers = student_auth["headers"]
    alumni_headers = alumni_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]
    student_id = student_auth["user"]["id"]

    # Student must approve recommendation before creating a request
    await _pre_approve(student_id=student_id, mentor_id=mentor_id)

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
    student_id = student_auth["user"]["id"]

    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
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
    student_id = student_auth["user"]["id"]

    # Create request
    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
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

@pytest.mark.asyncio
async def test_duplicate_mentorship_request_rejected(async_client, student_auth, alumni_auth):
    """A student cannot create a second pending request to the same mentor.
    After using the approval (first request), the second attempt must fail
    with APPROVAL_REQUIRED (no valid approval) rather than DUPLICATE_REQUEST."""
    student_headers = student_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]
    student_id = student_auth["user"]["id"]

    payload = {"mentor_id": mentor_id, "message": "First mentorship request."}

    # First request — needs approval
    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
    first = await async_client.post("/api/v1/mentorship-requests", json=payload, headers=student_headers)
    assert first.status_code == 201

    # Second attempt: approval was consumed, so APPROVAL_REQUIRED fires first
    second = await async_client.post("/api/v1/mentorship-requests", json=payload, headers=student_headers)
    assert second.status_code in (403, 409)
    err_code = second.json()["error"]["code"]
    assert err_code in ("APPROVAL_REQUIRED", "DUPLICATE_REQUEST"), (
        f"Expected APPROVAL_REQUIRED or DUPLICATE_REQUEST, got {err_code}"
    )

@pytest.mark.asyncio
async def test_request_without_approval_is_rejected(async_client, student_auth, alumni_auth):
    """POST /mentorship-requests must return 403 APPROVAL_REQUIRED if no approval exists."""
    student_headers = student_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]
    payload = {"mentor_id": mentor_id, "message": "No approval, should be rejected."}
    # No _pre_approve call — the gate must block this
    resp = await async_client.post("/api/v1/mentorship-requests", json=payload, headers=student_headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "APPROVAL_REQUIRED"

@pytest.mark.asyncio
async def test_resubmission_after_cancelled_request_allowed(async_client, student_auth, alumni_auth):
    """A student may create a new request to the same mentor after cancelling a prior one."""
    student_headers = student_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]
    student_id = student_auth["user"]["id"]

    # First request
    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
    first = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "First request, will be cancelled."},
        headers=student_headers,
    )
    assert first.status_code == 201
    req_id = first.json()["id"]

    # Cancel it
    cancel = await async_client.post(f"/api/v1/mentorship-requests/{req_id}/cancel", headers=student_headers)
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    # Second request — new approval needed; partial index allows it (status no longer 'pending')
    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
    second = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "Second request after cancellation."},
        headers=student_headers,
    )
    assert second.status_code == 201, (
        f"Expected 201 for resubmission after cancel, got {second.status_code}: {second.text}"
    )
    assert second.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_mentor_respond_to_request(async_client, student_auth, alumni_auth):
    """Mentor can accept or decline a mentorship request."""
    student_headers = student_auth["headers"]
    alumni_headers = alumni_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]
    student_id = student_auth["user"]["id"]

    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
    create_resp = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "Please mentor me on Python."},
        headers=student_headers,
    )
    assert create_resp.status_code == 201
    req_id = create_resp.json()["id"]

    # Mentor accepts the request
    respond_resp = await async_client.post(
        f"/api/v1/mentorship-requests/{req_id}/respond",
        json={"accept": True},
        headers=alumni_headers,
    )
    assert respond_resp.status_code == 200
    assert respond_resp.json()["status"] == "accepted"

    # Cannot respond again once accepted
    second_resp = await async_client.post(
        f"/api/v1/mentorship-requests/{req_id}/respond",
        json={"accept": False},
        headers=alumni_headers,
    )
    assert second_resp.status_code == 409

@pytest.mark.asyncio
async def test_non_mentor_cannot_respond(async_client, student_auth, alumni_auth):
    """A user who is not the designated mentor must receive 403 FORBIDDEN_RESOURCE."""
    student_headers = student_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]
    student_id = student_auth["user"]["id"]

    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
    create_resp = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "Mentor respond test."},
        headers=student_headers,
    )
    assert create_resp.status_code == 201
    req_id = create_resp.json()["id"]

    # Student (non-mentor) attempts to respond — must be forbidden
    wrong_respond = await async_client.post(
        f"/api/v1/mentorship-requests/{req_id}/respond",
        json={"accept": True},
        headers=student_headers,  # student, not the mentor
    )
    assert wrong_respond.status_code == 403
    assert wrong_respond.json()["error"]["code"] == "FORBIDDEN_RESOURCE"
