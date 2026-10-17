from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.core.database import get_database
from app.repositories.base import doc_to_dict

APPROVAL_TTL_MINUTES = 60


class MentorApprovalRepository:
    """
    Single-use approval tokens recording a student explicit acceptance of a
    specific mentor recommendation before a mentorship request is created.

    Lifecycle:
      POST /mentors/{mentor_id}/approve  -> creates/refreshes pending approval
      POST /mentorship-requests          -> consumes approval (pending -> consumed)

    Consumed or expired approvals cannot be replayed.
    """

    @property
    def collection(self):
        return get_database().mentor_approvals

    async def create_approval(self, student_id: str, mentor_id: str) -> Dict[str, Any]:
        """Create or refresh a pending approval for (student_id, mentor_id).
        Any prior pending approval for this pair is revoked and replaced."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=APPROVAL_TTL_MINUTES)
        # Revoke any existing pending token for this pair before issuing a fresh one
        await self.collection.delete_many(
            {"student_id": str(student_id), "mentor_id": str(mentor_id), "status": "pending"}
        )
        doc = {
            "student_id": str(student_id),
            "mentor_id": str(mentor_id),
            "status": "pending",
            "created_at": now,
            "expires_at": expires_at,
        }
        await self.collection.insert_one(doc)
        return doc_to_dict(doc)

    async def consume_approval(self, student_id: str, mentor_id: str) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        doc = await self.collection.find_one_and_update(
            {
                "student_id": str(student_id),
                "mentor_id": str(mentor_id),
                "status": "pending",
                "expires_at": {"$gt": now},
            },
            {"$set": {"status": "consumed", "consumed_at": now}},
            return_document=True,
        )
        return doc_to_dict(doc)

    async def get_pending_approval(self, student_id: str, mentor_id: str) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        doc = await self.collection.find_one({
            "student_id": str(student_id),
            "mentor_id": str(mentor_id),
            "status": "pending",
            "expires_at": {"$gt": now},
        })
        return doc_to_dict(doc)


mentor_approval_repo = MentorApprovalRepository()
