import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from app.repositories.community_repository import community_repo
from app.repositories.mentorship_repository import mentorship_repo
from app.repositories.profile_repository import profile_repo
from app.schemas.mentorship import MentorshipStatus

logger = logging.getLogger(__name__)

async def process_expired_requests(reference_time: Optional[datetime] = None) -> int:
    """
    Finds pending mentorship requests whose 48-hour deadline has passed,
    atomically transitions them to 'expired', finds next-mentor fallback,
    and notifies the student.
    Recovers seamlessly after server restarts.
    """
    now = reference_time or datetime.now(timezone.utc)
    expired_candidates = await mentorship_repo.find_expired_pending(now=now)
    processed_count = 0

    for req in expired_candidates:
        req_id = req["id"]
        # Find next mentor fallback
        student_id = req["student_id"]
        mentor_id = req["mentor_id"]
        fallback_mentor_id = None
        alumni_candidates = await profile_repo.list_alumni(limit=10, offset=0)
        for cand in alumni_candidates:
            if cand.get("user_id") not in [str(student_id), str(mentor_id)]:
                fallback_mentor_id = cand.get("user_id")
                break

        updated = await mentorship_repo.update_status(
            request_id=req_id,
            new_status=MentorshipStatus.EXPIRED.value,
            allowed_current_statuses=[MentorshipStatus.PENDING.value],
            fallback_recommendation_id=fallback_mentor_id,
        )

        if updated:
            processed_count += 1
            logger.info("Mentorship request %s expired after 48h deadline.", req_id)
            notif_msg = "Your mentorship request has expired after 48 hours without a mentor response."
            if fallback_mentor_id:
                notif_msg += " We have calculated your next recommended mentor."
            await community_repo.create_notification(
                user_id=student_id,
                title="Mentorship Request Expired",
                message=notif_msg,
                notif_type="request_expired",
                link=f"/mentorship-requests/{req_id}",
            )

    return processed_count

async def start_expiration_worker(poll_interval_seconds: int = 60):
    logger.info("Starting durable mentorship expiration worker (poll interval: %ds).", poll_interval_seconds)
    while True:
        try:
            await process_expired_requests()
        except asyncio.CancelledError:
            logger.info("Mentorship expiration worker cancelled.")
            break
        except Exception as e:
            logger.error("Error in mentorship expiration worker: %s", e)
        await asyncio.sleep(poll_interval_seconds)
