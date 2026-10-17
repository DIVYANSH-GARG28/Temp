import logging
from datetime import datetime, timezone
from typing import Any, Dict
from app.core.exceptions import AppException
from app.repositories.mentor_approval_repository import mentor_approval_repo
from app.repositories.profile_repository import profile_repo
from app.schemas.mentor import MentorApprovalResponse

logger = logging.getLogger(__name__)


class MentorApprovalService:
    async def approve(self, student_id: str, mentor_id: str) -> MentorApprovalResponse:
        # Verify the mentor exists and is accepting requests
        mentor_profile = await profile_repo.get_by_user_id(mentor_id)
        if not mentor_profile or mentor_profile.get("role") != "alumni":
            raise AppException(
                code="MENTOR_NOT_FOUND",
                message="Target mentor was not found or is not registered as an alumni.",
                status_code=404,
            )
        if not mentor_profile.get("mentorship_preferences", {}).get("accepting_requests", True):
            raise AppException(
                code="MENTOR_NOT_AVAILABLE",
                message="This mentor is not currently accepting mentorship requests.",
                status_code=400,
            )
        if str(mentor_id) == str(student_id):
            raise AppException(
                code="INVALID_REQUEST",
                message="You cannot approve yourself as a mentor.",
                status_code=400,
            )

        approval = await mentor_approval_repo.create_approval(
            student_id=str(student_id),
            mentor_id=str(mentor_id),
        )
        return MentorApprovalResponse(
            student_id=approval["student_id"],
            mentor_id=approval["mentor_id"],
            status=approval["status"],
            expires_at=approval["expires_at"],
        )


mentor_approval_service = MentorApprovalService()
