import pytest

@pytest.mark.asyncio
async def test_mentor_recommendations_contract(async_client, student_auth, alumni_auth):
    headers = student_auth["headers"]
    resp = await async_client.get("/api/v1/mentors/recommendations?limit=10&offset=0", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "algorithm_version" in data
    assert data["algorithm_version"] == "v1"
    assert "total" in data
    assert len(data["items"]) >= 1

    item = data["items"][0]
    assert "mentor_id" in item
    assert "name" in item
    assert "match_score" in item
    assert 0.0 <= item["match_score"] <= 1.0
    assert "reasons" in item
    assert len(item["reasons"]) > 0
    assert "code" in item["reasons"][0]
    assert "label" in item["reasons"][0]
    assert item["can_request"] is True

@pytest.mark.asyncio
async def test_mentor_recommendations_filter_and_pagination(async_client, student_auth, alumni_auth):
    headers = student_auth["headers"]
    resp = await async_client.get(
        "/api/v1/mentors/recommendations?skill=FastAPI&career_goal=Backend%20Engineering&limit=5&offset=0",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert len(data["items"]) >= 1
    assert data["items"][0]["mentor_id"] == alumni_auth["user"]["id"]
