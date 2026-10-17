import pytest
from app.core.config import settings
from tests.conftest import _pre_approve

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

    webhook_headers = {"X-Telegram-Bot-Api-Secret-Token": settings.TELEGRAM_WEBHOOK_SECRET} if settings.TELEGRAM_WEBHOOK_SECRET else {}

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
        headers=webhook_headers,
    )
    assert webhook_resp.status_code == 200
    wh_data = webhook_resp.json()
    assert wh_data["action"] == "link_account_success"

    # 3. Duplicate update is ignored
    dup_resp = await async_client.post(
        "/api/v1/webhooks/telegram",
        json=update_payload,
        headers=webhook_headers,
    )
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
    relink_resp = await async_client.post(
        "/api/v1/webhooks/telegram",
        json=relink_payload,
        headers=webhook_headers,
    )
    assert relink_resp.status_code == 200
    assert relink_resp.json()["action"] == "link_account_failed"

@pytest.mark.asyncio
async def test_telegram_mentor_callback_response(async_client, student_auth, alumni_auth):
    student_headers = student_auth["headers"]
    mentor_id = alumni_auth["user"]["id"]
    webhook_headers = {"X-Telegram-Bot-Api-Secret-Token": settings.TELEGRAM_WEBHOOK_SECRET} if settings.TELEGRAM_WEBHOOK_SECRET else {}

    # Link alumni to telegram chat 55555
    from app.repositories.user_repository import user_repo
    await user_repo.update_telegram_chat_id(mentor_id, "55555")

    # Student creates mentorship request (requires prior approval)
    student_id = student_auth["user"]["id"]
    await _pre_approve(student_id=student_id, mentor_id=mentor_id)
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
    cb_resp = await async_client.post(
        "/api/v1/webhooks/telegram",
        json=callback_update,
        headers=webhook_headers,
    )
    assert cb_resp.status_code == 200
    assert cb_resp.json()["action"] == "mentorship_accept"

    # Verify request is accepted
    check_req = await async_client.get(f"/api/v1/mentorship-requests/{req_id}", headers=student_headers)
    assert check_req.json()["status"] == "accepted"

@pytest.mark.asyncio
async def test_telegram_webhook_secret_authentication(async_client, monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", "super-secret-telegram-token")

    dummy_payload = {
        "update_id": 99001,
        "message": {"message_id": 1, "chat": {"id": 123}, "text": "/help"},
    }

    # 1. Request without secret header -> 401 Unauthorized
    resp_no_header = await async_client.post("/api/v1/webhooks/telegram", json=dummy_payload)
    assert resp_no_header.status_code == 401
    assert resp_no_header.json()["error"]["code"] == "UNAUTHORIZED_WEBHOOK"

    # 2. Request with incorrect secret header -> 401 Unauthorized
    resp_wrong_header = await async_client.post(
        "/api/v1/webhooks/telegram",
        json=dummy_payload,
        headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret-token"},
    )
    assert resp_wrong_header.status_code == 401
    assert resp_wrong_header.json()["error"]["code"] == "UNAUTHORIZED_WEBHOOK"

    # 3. Request with correct secret header -> 200 OK
    resp_valid = await async_client.post(
        "/api/v1/webhooks/telegram",
        json=dummy_payload,
        headers={"X-Telegram-Bot-Api-Secret-Token": "super-secret-telegram-token"},
    )
    assert resp_valid.status_code == 200
    assert resp_valid.json()["ok"] is True

@pytest.mark.asyncio
async def test_telegram_webhook_production_misconfiguration(async_client, monkeypatch):
    # In production, an unset secret must not silently disable authentication
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)

    dummy_payload = {
        "update_id": 99002,
        "message": {"message_id": 2, "chat": {"id": 123}, "text": "/help"},
    }
    resp = await async_client.post("/api/v1/webhooks/telegram", json=dummy_payload)
    assert resp.status_code == 500
    assert resp.json()["error"]["code"] == "MISCONFIGURED_WEBHOOK_SECRET"

@pytest.mark.asyncio
async def test_telegram_webhook_malformed_updates_safe(async_client, monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", None)
    monkeypatch.setattr(settings, "APP_ENV", "development")

    # 1. Update with photo/document (no text)
    resp1 = await async_client.post(
        "/api/v1/webhooks/telegram",
        json={"update_id": 30001, "message": {"message_id": 10, "chat": {"id": 123}, "photo": []}},
    )
    assert resp1.status_code == 200
    assert resp1.json()["ok"] is True

    # 2. Update with empty chat
    resp2 = await async_client.post(
        "/api/v1/webhooks/telegram",
        json={"update_id": 30002, "message": {"message_id": 11, "chat": {}, "text": "/start"}},
    )
    assert resp2.status_code == 200
    assert resp2.json()["ok"] is True

    # 3. Callback query with malformed data
    resp3 = await async_client.post(
        "/api/v1/webhooks/telegram",
        json={"update_id": 30003, "callback_query": {"id": "c1", "from": {"id": 999}, "data": "malformed_data"}},
    )
    assert resp3.status_code == 200
    assert resp3.json()["ok"] is True

    # 4. Callback query with missing from user
    resp4 = await async_client.post(
        "/api/v1/webhooks/telegram",
        json={"update_id": 30004, "callback_query": {"id": "c2", "data": "action:accept:req_123"}},
    )
    assert resp4.status_code == 200
    assert resp4.json()["action"] == "malformed_callback"

@pytest.mark.asyncio
async def test_telegram_logs_do_not_expose_secret(async_client, monkeypatch, caplog):
    secret_val = "sensitive-webhook-secret-999"
    monkeypatch.setattr(settings, "TELEGRAM_WEBHOOK_SECRET", secret_val)

    with caplog.at_level("WARNING"):
        await async_client.post(
            "/api/v1/webhooks/telegram",
            json={"update_id": 40001, "message": {"text": "/test"}},
            headers={"X-Telegram-Bot-Api-Secret-Token": "bad-token"},
        )

    # Confirm the real secret is never printed in logged warnings or errors
    assert secret_val not in caplog.text

def test_telegram_script_sanitization():
    from scripts.telegram_webhook import sanitize_text, sanitize_url

    dummy_token = "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
    dummy_secret = "secret-token-xyz-123"

    url_with_token = f"https://api.telegram.org/bot{dummy_token}/setWebhook?secret_token={dummy_secret}"
    sanitized = sanitize_url(url_with_token, token=dummy_token, secret=dummy_secret)

    assert dummy_token not in sanitized
    assert dummy_secret not in sanitized
    assert "[REDACTED" in sanitized

    error_msg = f"Failed connecting to bot{dummy_token} with secret {dummy_secret}"
    sanitized_err = sanitize_text(error_msg, token=dummy_token, secret=dummy_secret)
    assert dummy_token not in sanitized_err
    assert dummy_secret not in sanitized_err



