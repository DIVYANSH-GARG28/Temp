import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings
from app.repositories.outbox_repository import outbox_repo

logger = logging.getLogger(__name__)

class OutboxService:
    def __init__(self):
        self._reconciliation_lock = asyncio.Lock()

    def build_mentorship_created_payload(
        self,
        request_doc: Dict[str, Any],
        student_user: Dict[str, Any],
        mentor_user: Dict[str, Any],
    ) -> Dict[str, Any]:
        req_id = str(request_doc["id"])
        deadline = request_doc["deadline"]
        deadline_str = deadline.isoformat() if isinstance(deadline, datetime) else str(deadline)
        created_at = request_doc["created_at"]
        created_at_str = created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)

        return {
            "event_id": f"evt_req_{req_id}",
            "event_type": "mentorship.request.created",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "request_id": req_id,
                "student_id": str(request_doc["student_id"]),
                "student_name": student_user.get("name", "A Student"),
                "mentor_id": str(request_doc["mentor_id"]),
                "mentor_name": mentor_user.get("name", "Mentor"),
                "mentor_telegram_chat_id": mentor_user.get("telegram_chat_id"),
                "telegram_linked": bool(mentor_user.get("telegram_chat_id")),
                "message": request_doc["message"],
                "deadline": deadline_str,
                "created_at": created_at_str,
                "actions": {
                    "accept_callback": f"action:accept:{req_id}",
                    "decline_callback": f"action:decline:{req_id}",
                },
            },
        }

    async def create_or_restore_outbox_event(
        self,
        request_doc: Dict[str, Any],
        student_user: Dict[str, Any],
        mentor_user: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        payload = self.build_mentorship_created_payload(request_doc, student_user, mentor_user)
        event_id = payload["event_id"]

        existing = await outbox_repo.get_by_event_id(event_id)
        if existing:
            logger.info("Outbox event %s already exists with status '%s'. Skipping restore.", event_id, existing.get("status"))
            return existing

        event_doc = {
            "event_id": event_id,
            "event_type": payload["event_type"],
            "request_id": str(request_doc["id"]),
            "target_url": settings.N8N_WEBHOOK_URL,
            "payload": payload,
            "status": "pending",
            "attempts": 0,
            "claim_token": None,
            "claimed_by": None,
            "lease_expires_at": None,
            "next_retry_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        try:
            return await outbox_repo.create_event(event_doc)
        except Exception as e:
            logger.warning("Concurrent or duplicate insert handled for event %s: %s", event_id, e)
            return await outbox_repo.get_by_event_id(event_id)

    async def publish_mentorship_created_event(
        self,
        request_doc: Dict[str, Any],
        student_user: Dict[str, Any],
        mentor_user: Dict[str, Any],
        client: Optional[httpx.AsyncClient] = None,
        worker_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        event = await self.create_or_restore_outbox_event(request_doc, student_user, mentor_user)
        if event and event.get("status") == "dispatched":
            return event
        event_id = event["event_id"] if event else f"evt_req_{request_doc['id']}"
        return await self.deliver_event(event_id, worker_id=worker_id, client=client)

    async def reconcile_missing_events(
        self,
        batch_size: int = 50,
        max_batches: int = 10,
        now: Optional[datetime] = None,
    ) -> int:
        if self._reconciliation_lock.locked():
            logger.info("Outbox reconciliation already in progress. Skipping overlapping run.")
            return 0

        async with self._reconciliation_lock:
            from app.repositories.mentorship_repository import mentorship_repo
            from app.repositories.user_repository import user_repo

            current_time = now or datetime.now(timezone.utc)
            restored_count = 0
            last_id = None

            for _ in range(max_batches):
                candidates = await mentorship_repo.find_pending_active_requests(
                    last_id=last_id,
                    limit=batch_size,
                    now=current_time,
                )
                if not candidates:
                    break

                candidate_map = {f"evt_req_{r['id']}": r for r in candidates}
                event_ids = list(candidate_map.keys())

                cursor = outbox_repo.collection.find(
                    {"event_id": {"$in": event_ids}},
                    {"event_id": 1, "_id": 0},
                )
                existing_docs = await cursor.to_list(length=len(event_ids))
                existing_ids = {d["event_id"] for d in existing_docs}

                missing = [r for eid, r in candidate_map.items() if eid not in existing_ids]

                for req in missing:
                    try:
                        current_req = await mentorship_repo.get_by_id(req["id"])
                        if not current_req or current_req.get("status") != "pending":
                            continue

                        student_user = await user_repo.get_by_id(req["student_id"]) or {}
                        mentor_user = await user_repo.get_by_id(req["mentor_id"]) or {}
                        created_evt = await self.create_or_restore_outbox_event(req, student_user, mentor_user)
                        if created_evt:
                            restored_count += 1
                            logger.info("Reconciled and restored missing outbox event %s", created_evt.get("event_id"))
                    except Exception as e:
                        logger.error("Error reconciling outbox event for request %s: %s", req.get("id"), e)

                last_id = candidates[-1].get("_raw_id")
                if len(candidates) < batch_size:
                    break

            return restored_count


    async def deliver_event(
        self,
        event_id: str,
        worker_id: Optional[str] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        w_id = worker_id or f"worker_{uuid.uuid4().hex[:8]}"

        # Atomically claim the event with an active lease
        claimed = await outbox_repo.claim_event(
            event_id=event_id,
            worker_id=w_id,
            lease_seconds=settings.OUTBOX_LEASE_SECONDS,
            max_retries=settings.OUTBOX_MAX_RETRIES,
        )

        if not claimed:
            existing = await outbox_repo.get_by_event_id(event_id)
            if existing and existing.get("status") == "dispatched":
                logger.info("Outbox event %s already successfully dispatched.", event_id)
                return existing
            logger.info("Outbox event %s could not be claimed by %s (in-flight or max retries reached).", event_id, w_id)
            return existing or {"status": "claim_failed", "event_id": event_id}

        return await self.deliver_claimed_event(claimed, worker_id=w_id, client=client)

    async def deliver_claimed_event(
        self,
        claimed_event: Dict[str, Any],
        worker_id: str,
        client: Optional[httpx.AsyncClient] = None,
    ) -> Dict[str, Any]:
        event_id = claimed_event["event_id"]
        claim_token = claimed_event.get("claim_token")

        # 1. Check if production authentication is strictly required but secret is missing
        if settings.N8N_WEBHOOK_REQUIRE_AUTH and not settings.N8N_WEBHOOK_SECRET:
            error_msg = "Outbound webhook authentication required by configuration, but N8N_WEBHOOK_SECRET is missing."
            logger.error("Outbox event %s aborted: %s", event_id, error_msg)
            res = await outbox_repo.mark_failed(
                event_id=event_id,
                claim_token=claim_token,
                error_msg=error_msg,
            )
            return res or {"status": "auth_configuration_error", "event_id": event_id, "error": error_msg}

        # 2. Check target webhook URL
        webhook_url = settings.N8N_WEBHOOK_URL
        if not webhook_url:
            logger.info("N8N_WEBHOOK_URL is not configured; skipping remote HTTP delivery for event %s.", event_id)
            res = await outbox_repo.mark_failed(
                event_id=event_id,
                claim_token=claim_token,
                error_msg="N8N_WEBHOOK_URL not configured",
            )
            return res or {"status": "failed", "event_id": event_id}

        timeout_sec = settings.OUTBOX_TIMEOUT_SECONDS
        headers = {
            "Content-Type": "application/json",
            "X-Event-ID": event_id,
            "X-Event-Type": claimed_event.get("event_type", "mentorship.request.created"),
        }
        if settings.N8N_WEBHOOK_SECRET:
            headers["X-N8N-Webhook-Secret"] = settings.N8N_WEBHOOK_SECRET

        try:
            if client is not None:
                resp = await client.post(webhook_url, json=claimed_event["payload"], headers=headers, timeout=timeout_sec)
            else:
                async with httpx.AsyncClient(timeout=timeout_sec) as http_client:
                    resp = await http_client.post(webhook_url, json=claimed_event["payload"], headers=headers)

            if 200 <= resp.status_code < 300:
                logger.info("Successfully delivered outbox event %s (HTTP %d).", event_id, resp.status_code)
                res = await outbox_repo.mark_dispatched(event_id, claim_token=claim_token, response_status=resp.status_code)
                if not res:
                    logger.warning("Worker %s with token %s could not mark dispatched (claim expired or superseded).", worker_id, claim_token)
                    return {"status": "stale_claim", "event_id": event_id}
                return res
            else:
                error_summary = f"Webhook responded with non-success status: {resp.status_code}"
                logger.warning("Outbox event %s delivery failed: %s", event_id, error_summary)
                attempts = claimed_event.get("attempts", 0) + 1
                next_retry = datetime.now(timezone.utc) + timedelta(seconds=min(300, 5 * (2 ** attempts)))
                res = await outbox_repo.mark_failed(
                    event_id=event_id,
                    claim_token=claim_token,
                    error_msg=error_summary,
                    response_status=resp.status_code,
                    next_retry_at=next_retry,
                )
                if not res:
                    logger.warning("Worker %s with token %s could not mark failed (claim expired or superseded).", worker_id, claim_token)
                    return {"status": "stale_claim", "event_id": event_id}
                return res

        except httpx.TimeoutException:
            error_summary = f"Delivery timed out after {timeout_sec}s (POST may have been processed downstream)"
            logger.warning("Outbox event %s timeout: %s", event_id, error_summary)
            attempts = claimed_event.get("attempts", 0) + 1
            next_retry = datetime.now(timezone.utc) + timedelta(seconds=min(300, 5 * (2 ** attempts)))
            res = await outbox_repo.mark_failed(
                event_id=event_id,
                claim_token=claim_token,
                error_msg=error_summary,
                next_retry_at=next_retry,
            )
            if not res:
                return {"status": "stale_claim", "event_id": event_id}
            return res

        except httpx.RequestError as e:
            error_summary = f"HTTP request error: {type(e).__name__}"
            logger.warning("Outbox event %s request error: %s", event_id, error_summary)
            attempts = claimed_event.get("attempts", 0) + 1
            next_retry = datetime.now(timezone.utc) + timedelta(seconds=min(300, 5 * (2 ** attempts)))
            res = await outbox_repo.mark_failed(
                event_id=event_id,
                claim_token=claim_token,
                error_msg=error_summary,
                next_retry_at=next_retry,
            )
            if not res:
                return {"status": "stale_claim", "event_id": event_id}
            return res

        except Exception as e:
            error_summary = f"Unexpected delivery error: {type(e).__name__}"
            logger.error("Outbox event %s unexpected error: %s", event_id, error_summary)
            res = await outbox_repo.mark_failed(
                event_id=event_id,
                claim_token=claim_token,
                error_msg=error_summary,
            )
            if not res:
                return {"status": "stale_claim", "event_id": event_id}
            return res

    async def retry_pending_events(
        self,
        worker_id: Optional[str] = None,
        limit: int = 50,
        client: Optional[httpx.AsyncClient] = None,
    ) -> int:
        w_id = worker_id or f"retry_worker_{uuid.uuid4().hex[:8]}"
        dispatched_count = 0
        for _ in range(limit):
            claimed = await outbox_repo.claim_next_retryable_event(
                worker_id=w_id,
                lease_seconds=settings.OUTBOX_LEASE_SECONDS,
                max_retries=settings.OUTBOX_MAX_RETRIES,
            )
            if not claimed:
                break
            res = await self.deliver_claimed_event(claimed, worker_id=w_id, client=client)
            if res and res.get("status") == "dispatched":
                dispatched_count += 1
        return dispatched_count

outbox_service = OutboxService()

