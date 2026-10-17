from datetime import datetime, timedelta, timezone
import pytest
from tests.conftest import _pre_approve
from app.services.mentorship_service import mentorship_service

@pytest.mark.asyncio
async def test_meeting_proposals_mutual_confirmation(async_client, student_auth, alumni_auth):
    student_headers = student_auth["headers"]
    alumni_headers = alumni_auth["headers"]
    student_id = student_auth["user"]["id"]
    mentor_id = alumni_auth["user"]["id"]

    # 1. Create mentorship request and accept it
    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
    create_resp = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "Mentorship for meeting coordination."},
        headers=student_headers,
    )
    req_id = create_resp.json()["id"]

    # Mentor accepts
    await mentorship_service.respond_to_request(mentor_id=mentor_id, request_id=req_id, accept=True)

    # 2. Student proposes a meeting time
    meeting_time = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
    proposal_resp = await async_client.post(
        f"/api/v1/mentorship-requests/{req_id}/meeting-proposals",
        json={
            "proposed_time": meeting_time,
            "timezone_str": "America/New_York",
            "note": "Initial intro call and roadmap discussion",
        },
        headers=student_headers,
    )
    assert proposal_resp.status_code == 201
    prop_data = proposal_resp.json()
    proposal_id = prop_data["id"]
    # Critical rule: Proposer acceptance alone does NOT confirm the meeting!
    assert prop_data["status"] == "proposed"

    # 3. List proposals
    list_resp = await async_client.get(
        f"/api/v1/mentorship-requests/{req_id}/meeting-proposals",
        headers=alumni_headers,
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) == 1

    # 4. Mentor accepts proposal -> status transitions to 'confirmed'
    respond_resp = await async_client.post(
        f"/api/v1/meeting-proposals/{proposal_id}/respond",
        json={"action": "accept", "note": "Sounds great, see you then!"},
        headers=alumni_headers,
    )
    assert respond_resp.status_code == 200
    updated_prop = respond_resp.json()
    assert updated_prop["status"] == "confirmed"
    assert updated_prop["responses"][student_id] == "accepted"
    assert updated_prop["responses"][mentor_id] == "accepted"

@pytest.mark.asyncio
async def test_meeting_proposal_decline(async_client, student_auth, alumni_auth):
    student_headers = student_auth["headers"]
    alumni_headers = alumni_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]
    student_id = student_auth["user"]["id"]

    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
    create_resp = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "Request for meeting decline test."},
        headers=student_headers,
    )
    req_id = create_resp.json()["id"]
    await mentorship_service.respond_to_request(mentor_id=mentor_id, request_id=req_id, accept=True)

    # Propose
    meeting_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    prop_resp = await async_client.post(
        f"/api/v1/mentorship-requests/{req_id}/meeting-proposals",
        json={"proposed_time": meeting_time, "timezone_str": "UTC"},
        headers=student_headers,
    )
    proposal_id = prop_resp.json()["id"]

    # Mentor declines
    decline_resp = await async_client.post(
        f"/api/v1/meeting-proposals/{proposal_id}/respond",
        json={"action": "decline", "note": "Conflict with work schedule."},
        headers=alumni_headers,
    )
    assert decline_resp.status_code == 200
    assert decline_resp.json()["status"] == "declined"
