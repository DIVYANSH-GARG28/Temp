import pytest

@pytest.mark.asyncio
async def test_faculty_recommendations_and_research(async_client, student_auth):
    headers = student_auth["headers"]

    # 1. Faculty recommendations
    fac_resp = await async_client.get("/api/v1/faculty/recommendations", headers=headers)
    assert fac_resp.status_code == 200
    fac_data = fac_resp.json()
    assert "items" in fac_data
    assert "total" in fac_data

    # 2. Research projects
    proj_resp = await async_client.get("/api/v1/research-projects", headers=headers)
    assert proj_resp.status_code == 200
    proj_data = proj_resp.json()
    assert "items" in proj_data
    assert "total" in proj_data

    # 3. Communities
    comm_resp = await async_client.get("/api/v1/communities", headers=headers)
    assert comm_resp.status_code == 200
    comm_data = comm_resp.json()
    assert "items" in comm_data

    # 4. Notifications
    notif_resp = await async_client.get("/api/v1/notifications", headers=headers)
    assert notif_resp.status_code == 200
    assert "items" in notif_resp.json()
