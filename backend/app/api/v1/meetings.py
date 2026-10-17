from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_user
from app.schemas.meeting import (
    MeetingProposalCreate,
    MeetingProposalRespond,
    MeetingProposalResponse,
    MeetingProposalsListResponse,
)
from app.services.meeting_service import meeting_service

router = APIRouter(tags=["Meeting Coordination"])

@router.get(
    "/mentorship-requests/{request_id}/meeting-proposals",
    response_model=MeetingProposalsListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_meeting_proposals(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    """List meeting proposals for an accepted mentorship request."""
    return await meeting_service.list_proposals(user_id=current_user["id"], request_id=request_id)

@router.post(
    "/mentorship-requests/{request_id}/meeting-proposals",
    response_model=MeetingProposalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_meeting_proposal(
    request_id: str,
    proposal: MeetingProposalCreate,
    current_user: dict = Depends(get_current_user),
):
    """Propose a meeting time for an accepted mentorship request."""
    return await meeting_service.create_proposal(
        user_id=current_user["id"],
        request_id=request_id,
        proposal=proposal,
    )

@router.post(
    "/meeting-proposals/{proposal_id}/respond",
    response_model=MeetingProposalResponse,
    status_code=status.HTTP_200_OK,
)
async def respond_to_meeting_proposal(
    proposal_id: str,
    respond: MeetingProposalRespond,
    current_user: dict = Depends(get_current_user),
):
    """Accept or decline a meeting proposal. Confirms only on mutual agreement."""
    return await meeting_service.respond_to_proposal(
        user_id=current_user["id"],
        proposal_id=proposal_id,
        respond=respond,
    )
