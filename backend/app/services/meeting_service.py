from datetime import datetime, timezone
from app.core.exceptions import AppException
from app.repositories.community_repository import community_repo
from app.repositories.meeting_repository import meeting_repo
from app.repositories.mentorship_repository import mentorship_repo
from app.schemas.meeting import (
    MeetingProposalCreate,
    MeetingProposalRespond,
    MeetingProposalResponse,
    MeetingProposalsListResponse,
    MeetingStatus,
    ProposalResponseAction,
)

class MeetingService:
    async def list_proposals(self, user_id: str, request_id: str) -> MeetingProposalsListResponse:
        req = await mentorship_repo.get_by_id(request_id)
        if not req:
            raise AppException(
                code="REQUEST_NOT_FOUND",
                message="Mentorship request not found.",
                status_code=404,
            )

        if req["student_id"] != str(user_id) and req["mentor_id"] != str(user_id):
            raise AppException(
                code="FORBIDDEN_RESOURCE",
                message="You are not authorized to view meeting proposals for this request.",
                status_code=403,
            )

        docs = await meeting_repo.list_by_request_id(request_id)
        items = [
            MeetingProposalResponse(
                id=d["id"],
                mentorship_request_id=d["mentorship_request_id"],
                proposer_id=d["proposer_id"],
                proposed_time=d["proposed_time"],
                timezone_str=d["timezone_str"],
                status=MeetingStatus(d["status"]),
                responses=d.get("responses", {}),
                note=d.get("note"),
                created_at=d["created_at"],
                updated_at=d["updated_at"],
            )
            for d in docs
        ]
        return MeetingProposalsListResponse(items=items, total=len(items))

    async def create_proposal(
        self,
        user_id: str,
        request_id: str,
        proposal: MeetingProposalCreate,
    ) -> MeetingProposalResponse:
        req = await mentorship_repo.get_by_id(request_id)
        if not req:
            raise AppException(
                code="REQUEST_NOT_FOUND",
                message="Mentorship request not found.",
                status_code=404,
            )

        if req["student_id"] != str(user_id) and req["mentor_id"] != str(user_id):
            raise AppException(
                code="FORBIDDEN_RESOURCE",
                message="You are not a participant in this mentorship request.",
                status_code=403,
            )

        if req["status"] != "accepted":
            raise AppException(
                code="INVALID_STATE",
                message="Meeting proposals can only be created for accepted mentorship requests.",
                status_code=400,
            )

        # Proposer automatically agrees to their own proposal, but it remains 'proposed' until counterparty agrees
        now = datetime.now(timezone.utc)
        data = {
            "mentorship_request_id": str(request_id),
            "proposer_id": str(user_id),
            "proposed_time": proposal.proposed_time,
            "timezone_str": proposal.timezone_str,
            "status": MeetingStatus.PROPOSED.value,
            "responses": {str(user_id): "accepted"},
            "note": proposal.note,
            "created_at": now,
            "updated_at": now,
        }
        created = await meeting_repo.create_proposal(data)

        # Notify other participant
        counterparty_id = req["mentor_id"] if str(user_id) == req["student_id"] else req["student_id"]
        await community_repo.create_notification(
            user_id=counterparty_id,
            title="New Meeting Time Proposed",
            message=f"A new meeting time has been proposed for your mentorship session.",
            notif_type="meeting_proposal",
            link=f"/mentorship-requests/{request_id}/meeting-proposals",
        )

        return MeetingProposalResponse(
            id=created["id"],
            mentorship_request_id=created["mentorship_request_id"],
            proposer_id=created["proposer_id"],
            proposed_time=created["proposed_time"],
            timezone_str=created["timezone_str"],
            status=MeetingStatus(created["status"]),
            responses=created.get("responses", {}),
            note=created.get("note"),
            created_at=created["created_at"],
            updated_at=created["updated_at"],
        )

    async def respond_to_proposal(
        self,
        user_id: str,
        proposal_id: str,
        respond: MeetingProposalRespond,
    ) -> MeetingProposalResponse:
        prop = await meeting_repo.get_by_id(proposal_id)
        if not prop:
            raise AppException(
                code="PROPOSAL_NOT_FOUND",
                message="Meeting proposal not found.",
                status_code=404,
            )

        req = await mentorship_repo.get_by_id(prop["mentorship_request_id"])
        if not req:
            raise AppException(
                code="REQUEST_NOT_FOUND",
                message="Associated mentorship request not found.",
                status_code=404,
            )

        if req["student_id"] != str(user_id) and req["mentor_id"] != str(user_id):
            raise AppException(
                code="FORBIDDEN_RESOURCE",
                message="You are not authorized to respond to this meeting proposal.",
                status_code=403,
            )

        if prop["status"] in [MeetingStatus.CONFIRMED.value, MeetingStatus.DECLINED.value, MeetingStatus.CANCELLED.value]:
            raise AppException(
                code="PROPOSAL_ALREADY_RESOLVED",
                message=f"This proposal is already in status '{prop['status']}'.",
                status_code=409,
            )

        responses = dict(prop.get("responses", {}))
        action_val = "accepted" if respond.action == ProposalResponseAction.ACCEPT else "declined"
        responses[str(user_id)] = action_val

        # Check mutual acceptance
        student_resp = responses.get(req["student_id"])
        mentor_resp = responses.get(req["mentor_id"])

        if respond.action == ProposalResponseAction.DECLINE:
            new_status = MeetingStatus.DECLINED.value
        elif student_resp == "accepted" and mentor_resp == "accepted":
            new_status = MeetingStatus.CONFIRMED.value
        else:
            new_status = MeetingStatus.ACCEPTED_BY_ONE.value

        updated = await meeting_repo.update_response(
            proposal_id=proposal_id,
            user_id=str(user_id),
            action=action_val,
            new_status=new_status,
        )

        # Notify participants if confirmed
        if new_status == MeetingStatus.CONFIRMED.value:
            for pid in [req["student_id"], req["mentor_id"]]:
                await community_repo.create_notification(
                    user_id=pid,
                    title="Meeting Confirmed!",
                    message=f"Both participants agreed to the meeting time: {prop['proposed_time'].isoformat()} ({prop['timezone_str']}).",
                    notif_type="meeting_confirmed",
                    link=f"/mentorship-requests/{req['id']}/meeting-proposals",
                )

        return MeetingProposalResponse(
            id=updated["id"],
            mentorship_request_id=updated["mentorship_request_id"],
            proposer_id=updated["proposer_id"],
            proposed_time=updated["proposed_time"],
            timezone_str=updated["timezone_str"],
            status=MeetingStatus(updated["status"]),
            responses=updated.get("responses", {}),
            note=updated.get("note"),
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
        )

meeting_service = MeetingService()
