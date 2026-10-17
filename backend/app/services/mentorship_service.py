import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from app.core.exceptions import AppException
from app.repositories.community_repository import community_repo
from app.repositories.mentorship_repository import mentorship_repo
from app.repositories.profile_repository import profile_repo
from app.repositories.user_repository import user_repo
from app.schemas.mentorship import (
    MentorshipRequestCancelResponse,
    MentorshipRequestCreate,
    MentorshipRequestResponse,
    MentorshipRequestsListResponse,
    MentorshipStatus,
)

logger = logging.getLogger(__name__)

class MentorshipService:
    async def create_request(self, student_id: str, req: MentorshipRequestCreate) -> MentorshipRequestResponse:
        # Validate mentor exists and is an alumni
        mentor_profile = await profile_repo.get_by_user_id(req.mentor_id)
        if not mentor_profile or mentor_profile.get("role") != "alumni":
            raise AppException(
                code="MENTOR_NOT_FOUND",
                message="Target mentor was not found or is not registered as an alumni.",
                status_code=404,
            )

        if str(req.mentor_id) == str(student_id):
            raise AppException(
                code="INVALID_REQUEST",
                message="You cannot request mentorship from yourself.",
                status_code=400,
            )

        # Check if mentor is accepting requests
        if not mentor_profile.get("mentorship_preferences", {}).get("accepting_requests", True):
            raise AppException(
                code="MENTOR_NOT_AVAILABLE",
                message="This mentor is no longer accepting requests.",
                status_code=400,
            )

        # Prevent duplicate pending requests from the same student to the same mentor
        existing = await mentorship_repo.find_existing_active_request(
            student_id=str(student_id), mentor_id=str(req.mentor_id)
        )
        if existing:
            raise AppException(
                code="DUPLICATE_REQUEST",
                message="You already have an active pending request to this mentor.",
                status_code=409,
            )

        # Require explicit prior approval of this specific mentor recommendation
        from app.repositories.mentor_approval_repository import mentor_approval_repo
        consumed = await mentor_approval_repo.consume_approval(
            student_id=str(student_id), mentor_id=str(req.mentor_id)
        )
        if not consumed:
            raise AppException(
                code="APPROVAL_REQUIRED",
                message=(
                    "You must explicitly approve this mentor recommendation before sending a request. "
                    "Call POST /api/v1/mentors/{mentor_id}/approve first."
                ),
                status_code=403,
            )

        # Calculate authoritative 48-hour deadline on backend
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(hours=48)

        data = {
            "student_id": str(student_id),
            "mentor_id": str(req.mentor_id),
            "message": req.message,
            "status": MentorshipStatus.PENDING.value,
            "created_at": now,
            "updated_at": now,
            "deadline": deadline,
            "response_at": None,
            "fallback_recommendation_id": None,
            "metadata": {},
        }
        created = await mentorship_repo.create_request(data)

        # Send internal notification to mentor
        student_user = await user_repo.get_by_id(student_id)
        student_name = student_user.get("name", "A student") if student_user else "A student"
        mentor_user = await user_repo.get_by_id(req.mentor_id) or {}
        await community_repo.create_notification(
            user_id=req.mentor_id,
            title="New Mentorship Request",
            message=f"{student_name} has requested your mentorship on connectED.",
            notif_type="mentorship_request",
            link=f"/mentorship-requests/{created['id']}",
        )

        # Reliable outbound event delivery via Transactional Outbox (e.g. to n8n / Telegram)
        try:
            from app.services.outbox_service import outbox_service
            await outbox_service.publish_mentorship_created_event(
                request_doc=created,
                student_user=student_user or {},
                mentor_user=mentor_user,
            )
        except Exception as e:
            # Outbound delivery failure must NEVER corrupt or reverse the persisted mentorship request
            logger.error("Outbox dispatch encountered an error for request %s: %s", created["id"], e)

        return MentorshipRequestResponse(
            id=created["id"],
            student_id=created["student_id"],
            mentor_id=created["mentor_id"],
            message=created["message"],
            status=MentorshipStatus(created["status"]),
            created_at=created["created_at"],
            updated_at=created["updated_at"],
            deadline=created["deadline"],
            response_at=created.get("response_at"),
            fallback_recommendation_id=created.get("fallback_recommendation_id"),
            metadata=created.get("metadata", {}),
        )

    async def list_user_requests(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> MentorshipRequestsListResponse:
        docs = await mentorship_repo.list_for_user(user_id=user_id, status=status, limit=limit, offset=offset)
        total = await mentorship_repo.count_for_user(user_id=user_id, status=status)
        items = [
            MentorshipRequestResponse(
                id=d["id"],
                student_id=d["student_id"],
                mentor_id=d["mentor_id"],
                message=d["message"],
                status=MentorshipStatus(d["status"]),
                created_at=d["created_at"],
                updated_at=d["updated_at"],
                deadline=d["deadline"],
                response_at=d.get("response_at"),
                fallback_recommendation_id=d.get("fallback_recommendation_id"),
                metadata=d.get("metadata", {}),
            )
            for d in docs
        ]
        return MentorshipRequestsListResponse(items=items, total=total, limit=limit, offset=offset)

    async def get_request(self, user_id: str, request_id: str) -> MentorshipRequestResponse:
        req = await mentorship_repo.get_by_id(request_id)
        if not req:
            raise AppException(
                code="REQUEST_NOT_FOUND",
                message="Mentorship request not found.",
                status_code=404,
            )

        # Resource-level authorization: Requester or Mentor only
        if req["student_id"] != str(user_id) and req["mentor_id"] != str(user_id):
            raise AppException(
                code="FORBIDDEN_RESOURCE",
                message="You are not authorized to view this mentorship request.",
                status_code=403,
            )

        return MentorshipRequestResponse(
            id=req["id"],
            student_id=req["student_id"],
            mentor_id=req["mentor_id"],
            message=req["message"],
            status=MentorshipStatus(req["status"]),
            created_at=req["created_at"],
            updated_at=req["updated_at"],
            deadline=req["deadline"],
            response_at=req.get("response_at"),
            fallback_recommendation_id=req.get("fallback_recommendation_id"),
            metadata=req.get("metadata", {}),
        )

    async def cancel_request(self, user_id: str, request_id: str) -> MentorshipRequestCancelResponse:
        req = await mentorship_repo.get_by_id(request_id)
        if not req:
            raise AppException(
                code="REQUEST_NOT_FOUND",
                message="Mentorship request not found.",
                status_code=404,
            )

        if req["student_id"] != str(user_id):
            raise AppException(
                code="FORBIDDEN_RESOURCE",
                message="Only the student who created the request can cancel it.",
                status_code=403,
            )

        if req["status"] != MentorshipStatus.PENDING.value:
            raise AppException(
                code="INVALID_STATE_TRANSITION",
                message=f"Cannot cancel a request that is already '{req['status']}'.",
                status_code=409,
            )

        updated = await mentorship_repo.update_status(
            request_id=request_id,
            new_status=MentorshipStatus.CANCELLED.value,
            allowed_current_statuses=[MentorshipStatus.PENDING.value],
        )
        if not updated:
            raise AppException(
                code="CONFLICT",
                message="Request status was modified concurrently.",
                status_code=409,
            )

        return MentorshipRequestCancelResponse(
            id=updated["id"],
            status=MentorshipStatus.CANCELLED,
            message="Mentorship request cancelled successfully.",
            updated_at=updated["updated_at"],
        )

    async def respond_to_request(
        self,
        mentor_id: str,
        request_id: str,
        accept: bool,
    ) -> MentorshipRequestResponse:
        req = await mentorship_repo.get_by_id(request_id)
        if not req:
            raise AppException(
                code="REQUEST_NOT_FOUND",
                message="Mentorship request not found.",
                status_code=404,
            )

        if req["mentor_id"] != str(mentor_id):
            raise AppException(
                code="FORBIDDEN_RESOURCE",
                message="Only the designated mentor can respond to this request.",
                status_code=403,
            )

        if req["status"] != MentorshipStatus.PENDING.value:
            raise AppException(
                code="INVALID_STATE_TRANSITION",
                message=f"Cannot respond to a request that is already '{req['status']}'.",
                status_code=409,
            )

        now = datetime.now(timezone.utc)
        new_status = MentorshipStatus.ACCEPTED.value if accept else MentorshipStatus.DECLINED.value

        fallback_mentor_id = None
        if not accept:
            # Calculate next suitable mentor fallback
            fallback_mentor_id = await self._find_fallback_mentor(req["student_id"], req["mentor_id"])

        updated = await mentorship_repo.update_status(
            request_id=request_id,
            new_status=new_status,
            allowed_current_statuses=[MentorshipStatus.PENDING.value],
            response_at=now,
            fallback_recommendation_id=fallback_mentor_id,
        )
        if not updated:
            raise AppException(
                code="CONFLICT",
                message="Request was already processed or updated concurrently.",
                status_code=409,
            )

        # Notify student
        mentor_user = await user_repo.get_by_id(mentor_id)
        mentor_name = mentor_user.get("name", "The mentor") if mentor_user else "The mentor"
        action_text = "accepted" if accept else "declined"
        notif_msg = f"{mentor_name} has {action_text} your mentorship request."
        if not accept and fallback_mentor_id:
            notif_msg += " We have calculated your next recommended mentor."

        await community_repo.create_notification(
            user_id=req["student_id"],
            title=f"Mentorship Request {action_text.capitalize()}",
            message=notif_msg,
            notif_type="mentorship_response",
            link=f"/mentorship-requests/{request_id}",
        )

        return MentorshipRequestResponse(
            id=updated["id"],
            student_id=updated["student_id"],
            mentor_id=updated["mentor_id"],
            message=updated["message"],
            status=MentorshipStatus(updated["status"]),
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
            deadline=updated["deadline"],
            response_at=updated.get("response_at"),
            fallback_recommendation_id=updated.get("fallback_recommendation_id"),
            metadata=updated.get("metadata", {}),
        )

    async def _find_fallback_mentor(self, student_id: str, excluded_mentor_id: str) -> Optional[str]:
        candidates = await profile_repo.list_alumni(limit=10, offset=0)
        for cand in candidates:
            if cand.get("user_id") not in [str(student_id), str(excluded_mentor_id)]:
                return cand.get("user_id")
        return None

mentorship_service = MentorshipService()
