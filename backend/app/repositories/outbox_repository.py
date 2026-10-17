import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from app.core.database import get_database
from app.repositories.base import doc_to_dict

class OutboxRepository:
    @property
    def collection(self):
        return get_database().outbox_events

    async def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        event_data["created_at"] = event_data.get("created_at") or now
        event_data["updated_at"] = now
        event_data["status"] = event_data.get("status", "pending")
        event_data["attempts"] = event_data.get("attempts", 0)
        event_data["claim_token"] = event_data.get("claim_token")
        event_data["claimed_by"] = event_data.get("claimed_by")
        event_data["lease_expires_at"] = event_data.get("lease_expires_at")
        event_data["next_retry_at"] = event_data.get("next_retry_at")
        await self.collection.insert_one(event_data)
        return doc_to_dict(event_data)

    async def get_by_event_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"event_id": str(event_id)})
        return doc_to_dict(doc)

    async def claim_event(
        self,
        event_id: str,
        worker_id: str,
        lease_seconds: int = 30,
        max_retries: int = 3,
        now: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        current_time = now or datetime.now(timezone.utc)
        claim_token = str(uuid.uuid4())
        lease_expires_at = current_time + timedelta(seconds=lease_seconds)

        query = {
            "event_id": str(event_id),
            "attempts": {"$lt": max_retries},
            "$or": [
                {
                    "status": {"$in": ["pending", "failed"]},
                    "$or": [
                        {"next_retry_at": None},
                        {"next_retry_at": {"$lte": current_time}},
                    ],
                },
                {
                    "status": "processing",
                    "lease_expires_at": {"$lte": current_time},
                },
            ],
        }
        update = {
            "$set": {
                "status": "processing",
                "claimed_by": worker_id,
                "claim_token": claim_token,
                "lease_expires_at": lease_expires_at,
                "updated_at": current_time,
            }
        }
        doc = await self.collection.find_one_and_update(
            query,
            update,
            return_document=True,
        )
        return doc_to_dict(doc)

    async def claim_next_retryable_event(
        self,
        worker_id: str,
        lease_seconds: int = 30,
        max_retries: int = 3,
        now: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        current_time = now or datetime.now(timezone.utc)
        claim_token = str(uuid.uuid4())
        lease_expires_at = current_time + timedelta(seconds=lease_seconds)

        query = {
            "attempts": {"$lt": max_retries},
            "$or": [
                {
                    "status": {"$in": ["pending", "failed"]},
                    "$or": [
                        {"next_retry_at": None},
                        {"next_retry_at": {"$lte": current_time}},
                    ],
                },
                {
                    "status": "processing",
                    "lease_expires_at": {"$lte": current_time},
                },
            ],
        }
        update = {
            "$set": {
                "status": "processing",
                "claimed_by": worker_id,
                "claim_token": claim_token,
                "lease_expires_at": lease_expires_at,
                "updated_at": current_time,
            }
        }
        doc = await self.collection.find_one_and_update(
            query,
            update,
            sort=[("created_at", 1)],
            return_document=True,
        )
        return doc_to_dict(doc)

    async def mark_dispatched(
        self,
        event_id: str,
        claim_token: Optional[str] = None,
        response_status: int = 200,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        query: Dict[str, Any] = {"event_id": str(event_id)}
        if claim_token is not None:
            query["claim_token"] = claim_token
            query["status"] = "processing"

        doc = await self.collection.find_one_and_update(
            query,
            {
                "$set": {
                    "status": "dispatched",
                    "response_status": response_status,
                    "dispatched_at": now,
                    "updated_at": now,
                    "lease_expires_at": None,
                    "claim_token": None,
                },
                "$inc": {"attempts": 1},
            },
            return_document=True,
        )
        return doc_to_dict(doc)

    async def mark_failed(
        self,
        event_id: str,
        claim_token: Optional[str] = None,
        error_msg: str = "",
        response_status: Optional[int] = None,
        next_retry_at: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        query: Dict[str, Any] = {"event_id": str(event_id)}
        if claim_token is not None:
            query["claim_token"] = claim_token
            query["status"] = "processing"

        set_fields: Dict[str, Any] = {
            "status": "failed",
            "last_error": error_msg,
            "updated_at": now,
            "lease_expires_at": None,
            "claim_token": None,
        }
        if response_status is not None:
            set_fields["response_status"] = response_status
        if next_retry_at is not None:
            set_fields["next_retry_at"] = next_retry_at

        doc = await self.collection.find_one_and_update(
            query,
            {
                "$set": set_fields,
                "$inc": {"attempts": 1},
            },
            return_document=True,
        )
        return doc_to_dict(doc)

    async def find_pending_or_retryable(
        self,
        max_retries: int = 3,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        current_time = now or datetime.now(timezone.utc)
        query = {
            "attempts": {"$lt": max_retries},
            "$or": [
                {
                    "status": {"$in": ["pending", "failed"]},
                    "$or": [
                        {"next_retry_at": None},
                        {"next_retry_at": {"$lte": current_time}},
                    ],
                },
                {
                    "status": "processing",
                    "lease_expires_at": {"$lte": current_time},
                },
            ],
        }
        cursor = self.collection.find(query).limit(50)
        docs = await cursor.to_list(length=50)
        return [doc_to_dict(d) for d in docs]

outbox_repo = OutboxRepository()

