import pytest
from app.core.config import settings

@pytest.mark.asyncio
async def test_telegram_linking_and_webhook_flow(async_client, alumni_auth):
    headers = alumni_auth["headers"]
    alumni_id = alumni_auth["user"]["id"]

    # 1. Initiate linking
    init_resp = await async_client.post("/api/v1/telegram/link/initiate", headers=headers)
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    token = init_data["linking_token"]
    assert "deep_link" in init_data

    # 2. Simulate Telegram bot /start webhook delivery
    update_payload = {
        "update_id": 10001,
        "message": {
            "message_id": 55,
            "chat": {"id": 987654321},
            "text": f"/start link_{token}",
        },
    }
    webhook_resp = await async_client.post(
        "/api/v1/webhooks/telegram",
        json=update_payload,
    )
    assert webhook_resp.status_code == 200
    wh_data = webhook_resp.json()
    assert wh_data["action"] == "link_account_success"

    # 3. Duplicate update is ignored
    dup_resp = await async_client.post("/api/v1/webhooks/telegram", json=update_payload)
    assert dup_resp.status_code == 200
    assert dup_resp.json()["processed"] is False

    # 4. Consumed token cannot be reused
    relink_payload = {
        "update_id": 10002,
        "message": {
            "message_id": 56,
            "chat": {"id": 12345},
            "text": f"/start link_{token}",
        },
    }
    relink_resp = await async_client.post("/api/v1/webhooks/telegram", json=relink_payload)
    assert relink_resp.status_code == 200
    assert relink_resp.json()["action"] == "link_account_failed"

@pytest.mark.asyncio
async def test_telegram_mentor_callback_response(async_client, student_auth, alumni_auth):
    student_headers = student_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]

    # Link alumni to telegram chat 55555
    from app.repositories.user_repository import user_repo
    await user_repo.update_telegram_chat_id(mentor_id, "55555")

    # Student creates mentorship request
    req_resp = await async_client.post(
        "/api/v1/mentorship-requests",
        json={"mentor_id": mentor_id, "message": "Telegram callback response test."},
        headers=student_headers,
    )
    req_id = req_resp.json()["id"]

    # Telegram deliver callback query: action:accept:<req_id>
    callback_update = {
        "update_id": 20001,
        "callback_query": {
            "id": "cb_1",
            "from": {"id": 55555},
            "data": f"action:accept:{req_id}",
        },
    }
    cb_resp = await async_client.post("/api/v1/webhooks/telegram", json=callback_update)
    assert cb_resp.status_code == 200
    assert cb_resp.json()["action"] == "mentorship_accept"

    # Verify request is accepted
    check_req = await async_client.get(f"/api/v1/mentorship-requests/{req_id}", headers=student_headers)
    assert check_req.json()["status"] == "accepted"
