from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user
from app.schemas.mentorship import (
    MentorshipRequestCancelResponse,
    MentorshipRequestCreate,
    MentorshipRequestResponse,
    MentorshipRequestsListResponse,
)
from app.services.mentorship_service import mentorship_service

router = APIRouter(prefix="/mentorship-requests", tags=["Mentorship Requests"])

@router.post("", response_model=MentorshipRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_mentorship_request(
    req: MentorshipRequestCreate,
    current_user: dict = Depends(get_current_user),
):
    """Explicitly create a mentorship request with a backend-authoritative 48-hour response deadline."""
    return await mentorship_service.create_request(student_id=current_user["id"], req=req)

@router.get("", response_model=MentorshipRequestsListResponse, status_code=status.HTTP_200_OK)
async def list_mentorship_requests(
    status: Optional[str] = Query(None, description="Filter by status (pending, accepted, declined, expired, cancelled)"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """List mentorship requests visible to the current authenticated user."""
    return await mentorship_service.list_user_requests(
        user_id=current_user["id"],
        status=status,
        limit=limit,
        offset=offset,
    )

@router.get("/{request_id}", response_model=MentorshipRequestResponse, status_code=status.HTTP_200_OK)
async def get_mentorship_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve details of a specific mentorship request."""
    return await mentorship_service.get_request(user_id=current_user["id"], request_id=request_id)

@router.post("/{request_id}/cancel", response_model=MentorshipRequestCancelResponse, status_code=status.HTTP_200_OK)
async def cancel_mentorship_request(
    request_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Cancel an eligible pending mentorship request."""
    return await mentorship_service.cancel_request(user_id=current_user["id"], request_id=request_id)
