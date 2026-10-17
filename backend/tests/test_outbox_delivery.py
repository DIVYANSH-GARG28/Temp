import logging
from unittest.mock import patch
import httpx
import pytest
import pytest_asyncio
from app.core.config import settings
from app.repositories.outbox_repository import outbox_repo
from tests.conftest import _pre_approve

@pytest_asyncio.fixture(autouse=True)
async def pre_approve_for_outbox_tests(student_auth, alumni_auth):
    """
    Pre-seed an approval token before each outbox test so that
    POST /mentorship-requests is not blocked by the approval gate.
    Each outbox test consumes one approval; tests that create multiple
    requests must call _pre_approve explicitly between creates.
    """
    student_id = student_auth["user"]["id"]
    mentor_id = alumni_auth["user"]["id"]
    await _pre_approve(student_id=student_id, mentor_id=mentor_id)


@pytest.mark.asyncio
async def test_successful_outbox_delivery(async_client, student_auth, alumni_auth, monkeypatch):
    webhook_url = "https://mock.webhook.test/events"
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", webhook_url)

    delivered_requests = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        delivered_requests.append(request)
        return httpx.Response(200, json={"status": "received"})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))

    with patch("httpx.AsyncClient", return_value=mock_client):
        resp = await async_client.post(
            "/api/v1/mentorship-requests",
            json={"mentor_id": alumni_auth["user"]["id"], "message": "Mentorship with outbox delivery."},
            headers=student_auth["headers"],
        )
    assert resp.status_code == 201
    req_id = resp.json()["id"]

    event = await outbox_repo.get_by_event_id(f"evt_req_{req_id}")
    assert event is not None
    assert event["status"] == "dispatched"
    assert event["response_status"] == 200
    assert event["payload"]["data"]["request_id"] == req_id
    assert event["payload"]["data"]["student_name"] == "Jane Student"
    assert event["payload"]["data"]["actions"]["accept_callback"] == f"action:accept:{req_id}"

@pytest.mark.asyncio
async def test_outbox_delivery_timeout_does_not_abort_request(async_client, student_auth, alumni_auth, monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "https://mock.webhook.test/timeout")

    def mock_timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Mocked timeout")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_timeout_handler))

    with patch("httpx.AsyncClient", return_value=mock_client):
        resp = await async_client.post(
            "/api/v1/mentorship-requests",
            json={"mentor_id": alumni_auth["user"]["id"], "message": "Mentorship with timeout webhook."},
            headers=student_auth["headers"],
        )
    # Request MUST be persisted and return 201 Created even if webhook times out
    assert resp.status_code == 201
    req_id = resp.json()["id"]

    event = await outbox_repo.get_by_event_id(f"evt_req_{req_id}")
    assert event is not None
    assert event["status"] == "failed"
    assert "timed out" in event["last_error"]
    assert event["attempts"] == 1

@pytest.mark.asyncio
async def test_outbox_delivery_non_success_status(async_client, student_auth, alumni_auth, monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "https://mock.webhook.test/500")

    def mock_error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "Internal Server Error"})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_error_handler))

    with patch("httpx.AsyncClient", return_value=mock_client):
        resp = await async_client.post(
            "/api/v1/mentorship-requests",
            json={"mentor_id": alumni_auth["user"]["id"], "message": "Mentorship with error webhook."},
            headers=student_auth["headers"],
        )
    assert resp.status_code == 201
    req_id = resp.json()["id"]

    event = await outbox_repo.get_by_event_id(f"evt_req_{req_id}")
    assert event is not None
    assert event["status"] == "failed"
    assert event["response_status"] == 500
    assert "non-success" in event["last_error"]

@pytest.mark.asyncio
async def test_outbox_duplicate_event_handling(async_client, student_auth, alumni_auth, monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "https://mock.webhook.test/duplicate")
    dispatch_counter = 0

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal dispatch_counter
        dispatch_counter += 1
        return httpx.Response(200, json={"ok": True})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    from app.services.outbox_service import outbox_service

    with patch("httpx.AsyncClient", return_value=mock_client):
        resp = await async_client.post(
            "/api/v1/mentorship-requests",
            json={"mentor_id": alumni_auth["user"]["id"], "message": "Test duplicate event handling."},
            headers=student_auth["headers"],
        )
    assert resp.status_code == 201
    req_id = resp.json()["id"]
    event_id = f"evt_req_{req_id}"

    # Try duplicate publish with same event_id
    fake_doc = {"id": req_id, "student_id": "s1", "mentor_id": "m1", "message": "msg", "deadline": "2026-10-20", "created_at": "2026-10-18"}
    res = await outbox_service.publish_mentorship_created_event(fake_doc, {}, {}, client=mock_client)
    assert res["event_id"] == event_id
    assert dispatch_counter == 1

@pytest.mark.asyncio
async def test_no_secrets_in_outbox_payload_or_logs(async_client, student_auth, alumni_auth, monkeypatch, caplog):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "https://mock.webhook.test/secret-check")

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200)))

    with patch("httpx.AsyncClient", return_value=mock_client):
        with caplog.at_level(logging.DEBUG):
            resp = await async_client.post(
                "/api/v1/mentorship-requests",
                json={"mentor_id": alumni_auth["user"]["id"], "message": "Mentorship secret safety check."},
                headers=student_auth["headers"],
            )
    assert resp.status_code == 201
    req_id = resp.json()["id"]

    event = await outbox_repo.get_by_event_id(f"evt_req_{req_id}")
    assert event is not None
    payload = event["payload"]
    payload_str = str(payload)

    # Ensure sensitive settings are not present in payload
    assert settings.JWT_SECRET_KEY not in payload_str
    if settings.TELEGRAM_BOT_TOKEN:
        assert settings.TELEGRAM_BOT_TOKEN not in payload_str
    if settings.TELEGRAM_WEBHOOK_SECRET:
        assert settings.TELEGRAM_WEBHOOK_SECRET not in payload_str

    # Ensure user passwords/hashes are not present in payload data
    assert "hashed_password" not in payload_str
    assert student_auth["user"]["hashed_password"] not in payload_str
    assert "password" not in payload["data"]

    # Ensure sensitive credentials are not leaked to application logs
    logs_str = caplog.text
    assert settings.JWT_SECRET_KEY not in logs_str
    if settings.TELEGRAM_BOT_TOKEN:
        assert settings.TELEGRAM_BOT_TOKEN not in logs_str
    if settings.TELEGRAM_WEBHOOK_SECRET:
        assert settings.TELEGRAM_WEBHOOK_SECRET not in logs_str

@pytest.mark.asyncio
async def test_configured_webhook_authentication(async_client, student_auth, alumni_auth, monkeypatch, caplog):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "https://mock.webhook.test/auth-test")
    monkeypatch.setattr(settings, "N8N_WEBHOOK_SECRET", "super-secret-n8n-token-123")

    captured_headers = {}

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_headers
        captured_headers = dict(request.headers)
        return httpx.Response(200, json={"status": "authenticated"})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))

    with patch("httpx.AsyncClient", return_value=mock_client):
        with caplog.at_level(logging.DEBUG):
            resp = await async_client.post(
                "/api/v1/mentorship-requests",
                json={"mentor_id": alumni_auth["user"]["id"], "message": "Auth header test."},
                headers=student_auth["headers"],
            )
    assert resp.status_code == 201
    assert captured_headers.get("x-n8n-webhook-secret") == "super-secret-n8n-token-123"
    assert "super-secret-n8n-token-123" not in caplog.text

@pytest.mark.asyncio
async def test_missing_required_production_secret(async_client, student_auth, alumni_auth, monkeypatch):
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "https://mock.webhook.test/strict-auth")
    monkeypatch.setattr(settings, "N8N_WEBHOOK_REQUIRE_AUTH", True)
    monkeypatch.setattr(settings, "N8N_WEBHOOK_SECRET", None)

    dispatched = False

    def mock_handler(request: httpx.Request) -> httpx.Response:
        nonlocal dispatched
        dispatched = True
        return httpx.Response(200)

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))

    with patch("httpx.AsyncClient", return_value=mock_client):
        resp = await async_client.post(
            "/api/v1/mentorship-requests",
            json={"mentor_id": alumni_auth["user"]["id"], "message": "Strict auth check."},
            headers=student_auth["headers"],
        )
    # Request is created safely without failing API
    assert resp.status_code == 201
    req_id = resp.json()["id"]

    # Delivery must be aborted without sending external HTTP requests
    assert dispatched is False
    event = await outbox_repo.get_by_event_id(f"evt_req_{req_id}")
    assert event is not None
    assert event["status"] == "failed"
    assert "authentication required" in event["last_error"]

@pytest.mark.asyncio
async def test_atomic_claiming_and_competing_workers(monkeypatch):
    from datetime import datetime, timezone
    from app.repositories.outbox_repository import outbox_repo

    now = datetime.now(timezone.utc)
    event_id = "evt_compete_123"
    await outbox_repo.create_event({
        "event_id": event_id,
        "event_type": "mentorship.request.created",
        "status": "pending",
        "attempts": 0,
        "created_at": now,
    })

    # Worker A claims the event
    claim_a = await outbox_repo.claim_event(event_id, worker_id="worker_A", lease_seconds=30, now=now)
    assert claim_a is not None
    assert claim_a["status"] == "processing"
    assert claim_a["claimed_by"] == "worker_A"
    assert claim_a["claim_token"] is not None

    # Worker B concurrently attempts to claim the same event while Worker A's lease is active
    claim_b = await outbox_repo.claim_event(event_id, worker_id="worker_B", lease_seconds=30, now=now)
    assert claim_b is None

@pytest.mark.asyncio
async def test_lease_expiry_and_recovery(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from app.repositories.outbox_repository import outbox_repo

    t0 = datetime.now(timezone.utc)
    event_id = "evt_expire_456"
    await outbox_repo.create_event({
        "event_id": event_id,
        "event_type": "mentorship.request.created",
        "status": "pending",
        "attempts": 0,
        "created_at": t0,
    })

    # Worker A claims with a 2-second lease
    claim_a = await outbox_repo.claim_event(event_id, worker_id="worker_A", lease_seconds=2, now=t0)
    assert claim_a is not None

    # Worker B attempts to claim after lease expiry (3 seconds later)
    t1 = t0 + timedelta(seconds=3)
    claim_b = await outbox_repo.claim_event(event_id, worker_id="worker_B", lease_seconds=30, now=t1)
    assert claim_b is not None
    assert claim_b["claimed_by"] == "worker_B"
    assert claim_b["claim_token"] != claim_a["claim_token"]

@pytest.mark.asyncio
async def test_stale_worker_claim_cannot_overwrite_newer_state(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from app.repositories.outbox_repository import outbox_repo

    t0 = datetime.now(timezone.utc)
    event_id = "evt_stale_789"
    await outbox_repo.create_event({
        "event_id": event_id,
        "event_type": "mentorship.request.created",
        "status": "pending",
        "attempts": 0,
        "created_at": t0,
    })

    # 1. Worker A claims the event (receives Token A)
    claim_a = await outbox_repo.claim_event(event_id, worker_id="worker_A", lease_seconds=2, now=t0)
    token_a = claim_a["claim_token"]

    # 2. Worker A lags/crashes; Worker B reclaims after lease expires (receives Token B)
    t1 = t0 + timedelta(seconds=5)
    claim_b = await outbox_repo.claim_event(event_id, worker_id="worker_B", lease_seconds=30, now=t1)
    token_b = claim_b["claim_token"]
    assert token_b != token_a

    # 3. Worker B dispatches successfully
    res_b = await outbox_repo.mark_dispatched(event_id, claim_token=token_b, response_status=200)
    assert res_b is not None
    assert res_b["status"] == "dispatched"

    # 4. Stale Worker A wakes up and attempts to mark failed with stale Token A
    res_stale = await outbox_repo.mark_failed(event_id, claim_token=token_a, error_msg="Stale failure")
    # Must be rejected because claim_token does not match!
    assert res_stale is None

    # State in DB must still be dispatched by Worker B
    final_event = await outbox_repo.get_by_event_id(event_id)
    assert final_event["status"] == "dispatched"
    assert final_event["response_status"] == 200

@pytest.mark.asyncio
async def test_retry_limits_enforced(monkeypatch):
    from datetime import datetime, timezone
    from app.repositories.outbox_repository import outbox_repo

    now = datetime.now(timezone.utc)
    event_id = "evt_retry_limit_999"
    await outbox_repo.create_event({
        "event_id": event_id,
        "event_type": "mentorship.request.created",
        "status": "failed",
        "attempts": 3,
        "next_retry_at": None,
        "created_at": now,
    })

    # Attempt to claim when attempts == max_retries (3)
    claimed = await outbox_repo.claim_event(event_id, worker_id="worker_1", max_retries=3, now=now)
    assert claimed is None

    next_claimed = await outbox_repo.claim_next_retryable_event(worker_id="worker_1", max_retries=3, now=now)
    assert next_claimed is None

@pytest.mark.asyncio
async def test_reconciliation_restores_missing_outbox_event(student_auth, alumni_auth, monkeypatch):
    from datetime import datetime, timedelta, timezone
    from app.repositories.mentorship_repository import mentorship_repo
    from app.services.outbox_service import outbox_service

    now = datetime.now(timezone.utc)
    student_id = student_auth["user"]["id"]
    mentor_id = alumni_auth["user"]["id"]

    # 1. Mentorship request exists, but outbox event was never created (simulated crash)
    req = await mentorship_repo.create_request({
        "student_id": student_id,
        "mentor_id": mentor_id,
        "message": "Please mentor me on backend architecture.",
        "status": "pending",
        "created_at": now,
        "deadline": now + timedelta(hours=48),
    })
    req_id = req["id"]
    event_id = f"evt_req_{req_id}"

    # Verify no outbox event exists initially
    assert await outbox_repo.get_by_event_id(event_id) is None

    # 2. Run reconciliation
    restored = await outbox_service.reconcile_missing_events()
    assert restored >= 1

    # 3. Verify outbox event is restored with status="pending" and correct payload
    event = await outbox_repo.get_by_event_id(event_id)
    assert event is not None
    assert event["status"] == "pending"
    assert event["attempts"] == 0
    assert event["payload"]["data"]["request_id"] == req_id
    assert event["payload"]["data"]["student_name"] == "Jane Student"

    # 4. Outbox delivery engine can now pick it up and deliver it
    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200)))
    monkeypatch.setattr(settings, "N8N_WEBHOOK_URL", "https://mock.webhook.test/reconciled")
    dispatched = await outbox_service.retry_pending_events(client=mock_client)
    assert dispatched >= 1

    updated_event = await outbox_repo.get_by_event_id(event_id)
    assert updated_event["status"] == "dispatched"

@pytest.mark.asyncio
async def test_reconciliation_skips_existing_outbox_event(student_auth, alumni_auth):
    from datetime import datetime, timedelta, timezone
    from app.repositories.mentorship_repository import mentorship_repo
    from app.services.outbox_service import outbox_service

    now = datetime.now(timezone.utc)
    req = await mentorship_repo.create_request({
        "student_id": student_auth["user"]["id"],
        "mentor_id": alumni_auth["user"]["id"],
        "message": "Already has outbox event.",
        "status": "pending",
        "created_at": now,
        "deadline": now + timedelta(hours=48),
    })
    req_id = req["id"]
    event_id = f"evt_req_{req_id}"

    # Pre-create outbox event as dispatched
    await outbox_repo.create_event({
        "event_id": event_id,
        "event_type": "mentorship.request.created",
        "request_id": req_id,
        "status": "dispatched",
        "attempts": 1,
        "created_at": now,
    })

    restored = await outbox_service.reconcile_missing_events()
    # Should not restore or overwrite existing event
    event = await outbox_repo.get_by_event_id(event_id)
    assert event["status"] == "dispatched"

@pytest.mark.asyncio
async def test_reconciliation_duplicate_creation_races(student_auth, alumni_auth):
    import asyncio
    from datetime import datetime, timedelta, timezone
    from app.repositories.mentorship_repository import mentorship_repo
    from app.services.outbox_service import outbox_service

    now = datetime.now(timezone.utc)
    req = await mentorship_repo.create_request({
        "student_id": student_auth["user"]["id"],
        "mentor_id": alumni_auth["user"]["id"],
        "message": "Concurrent restore test.",
        "status": "pending",
        "created_at": now,
        "deadline": now + timedelta(hours=48),
    })
    event_id = f"evt_req_{req['id']}"

    # Simulate two workers attempting to restore the missing event at the exact same time
    results = await asyncio.gather(
        outbox_service.create_or_restore_outbox_event(req, student_auth["user"], alumni_auth["user"]),
        outbox_service.create_or_restore_outbox_event(req, student_auth["user"], alumni_auth["user"]),
        return_exceptions=True,
    )

    # Neither should crash with an unhandled DuplicateKeyError
    assert not isinstance(results[0], Exception)
    assert not isinstance(results[1], Exception)
    assert results[0]["event_id"] == event_id
    assert results[1]["event_id"] == event_id

@pytest.mark.asyncio
async def test_reconciliation_recovers_older_eligible_request(student_auth, alumni_auth):
    from datetime import datetime, timedelta, timezone
    from app.repositories.mentorship_repository import mentorship_repo
    from app.services.outbox_service import outbox_service

    # Outage occurred 24 hours ago; request created then is still eligible (24h before 48h deadline)
    now = datetime.now(timezone.utc)
    past_24h = now - timedelta(hours=24)
    req = await mentorship_repo.create_request({
        "student_id": student_auth["user"]["id"],
        "mentor_id": alumni_auth["user"]["id"],
        "message": "Created 24 hours ago during outage.",
        "status": "pending",
        "created_at": past_24h,
        "deadline": past_24h + timedelta(hours=48), # deadline is now + 24h
    })
    event_id = f"evt_req_{req['id']}"

    restored = await outbox_service.reconcile_missing_events()
    assert restored >= 1

    event = await outbox_repo.get_by_event_id(event_id)
    assert event is not None
    assert event["status"] == "pending"

@pytest.mark.asyncio
async def test_reconciliation_excludes_ineligible_requests(student_auth, alumni_auth):
    from datetime import datetime, timedelta, timezone
    from app.repositories.mentorship_repository import mentorship_repo
    from app.services.outbox_service import outbox_service

    now = datetime.now(timezone.utc)
    # 1. Cancelled request
    r_cancel = await mentorship_repo.create_request({
        "student_id": student_auth["user"]["id"],
        "mentor_id": alumni_auth["user"]["id"],
        "message": "Cancelled request.",
        "status": "cancelled",
        "created_at": now,
        "deadline": now + timedelta(hours=48),
    })
    # 2. Accepted request
    r_accept = await mentorship_repo.create_request({
        "student_id": student_auth["user"]["id"],
        "mentor_id": alumni_auth["user"]["id"],
        "message": "Accepted request.",
        "status": "accepted",
        "created_at": now,
        "deadline": now + timedelta(hours=48),
    })
    # 3. Declined request
    r_decline = await mentorship_repo.create_request({
        "student_id": student_auth["user"]["id"],
        "mentor_id": alumni_auth["user"]["id"],
        "message": "Declined request.",
        "status": "declined",
        "created_at": now,
        "deadline": now + timedelta(hours=48),
    })
    # 4. Past deadline request (expired)
    r_expired = await mentorship_repo.create_request({
        "student_id": student_auth["user"]["id"],
        "mentor_id": alumni_auth["user"]["id"],
        "message": "Past deadline request.",
        "status": "pending",
        "created_at": now - timedelta(hours=50),
        "deadline": now - timedelta(hours=2), # deadline has passed
    })

    restored = await outbox_service.reconcile_missing_events()

    # None of these should have outbox events created
    assert await outbox_repo.get_by_event_id(f"evt_req_{r_cancel['id']}") is None
    assert await outbox_repo.get_by_event_id(f"evt_req_{r_accept['id']}") is None
    assert await outbox_repo.get_by_event_id(f"evt_req_{r_decline['id']}") is None
    assert await outbox_repo.get_by_event_id(f"evt_req_{r_expired['id']}") is None

@pytest.mark.asyncio
async def test_reconciliation_bounded_pagination(student_auth, alumni_auth):
    from datetime import datetime, timedelta, timezone
    from app.repositories.mentorship_repository import mentorship_repo
    from app.services.outbox_service import outbox_service

    now = datetime.now(timezone.utc)
    student_id = student_auth["user"]["id"]
    # Create 5 pending requests without outbox events.
    # Each uses a distinct synthetic mentor_id so the partial unique index
    # on (student_id, mentor_id) where status='pending' is not violated.
    created_ids = []
    for i in range(5):
        r = await mentorship_repo.create_request({
            "student_id": student_id,
            "mentor_id": f"synthetic-mentor-{i}",
            "message": f"Batch pagination test request {i}.",
            "status": "pending",
            "created_at": now + timedelta(seconds=i),
            "deadline": now + timedelta(hours=48),
        })
        created_ids.append(r["id"])

    # Run reconciliation bounded to batch_size=2 and max_batches=2 (max 4 items processed)
    restored = await outbox_service.reconcile_missing_events(batch_size=2, max_batches=2)
    assert restored == 4

@pytest.mark.asyncio
async def test_reconciliation_failure_does_not_terminate_worker(monkeypatch):
    import asyncio
    from unittest.mock import AsyncMock
    from app.jobs.expiration_worker import start_expiration_worker
    from app.services.outbox_service import outbox_service


    # Simulate reconciliation throwing an unexpected database error
    mock_reconcile = AsyncMock(side_effect=RuntimeError("Simulated database timeout in reconciliation"))
    monkeypatch.setattr(outbox_service, "reconcile_missing_events", mock_reconcile)

    # Launch worker for 100ms then cancel it
    task = asyncio.create_task(start_expiration_worker(poll_interval_seconds=1))
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Worker caught the error and did not crash before being cancelled
    assert mock_reconcile.called



