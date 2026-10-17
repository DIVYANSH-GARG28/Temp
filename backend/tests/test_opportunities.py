import pytest

@pytest.mark.asyncio
async def test_opportunities_creation_and_listing(async_client, recruiter_auth, student_auth):
    recruiter_headers = recruiter_auth["headers"]
    student_headers = student_auth["headers"]

    # Student cannot create opportunity
    opp_payload = {
        "type": "internship",
        "title": "Software Engineering Intern",
        "description": "Summer 2027 internship working on high throughput APIs.",
        "organization": "TechCorp",
        "required_skills": ["Python", "FastAPI"],
    }
    student_create = await async_client.post("/api/v1/opportunities", json=opp_payload, headers=student_headers)
    assert student_create.status_code == 403
    assert student_create.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    # Recruiter can create opportunity
    recruiter_create = await async_client.post("/api/v1/opportunities", json=opp_payload, headers=recruiter_headers)
    assert recruiter_create.status_code == 201
    opp_data = recruiter_create.json()
    assert opp_data["title"] == "Software Engineering Intern"
    assert opp_data["type"] == "internship"
    assert opp_data["creator_id"] == recruiter_auth["user"]["id"]

    # Student can browse opportunities
    list_resp = await async_client.get("/api/v1/opportunities?type=internship", headers=student_headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) >= 1
