from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user
from app.schemas.mentor import MentorApprovalResponse, MentorRecommendationsResponse
from app.services.matching_service import matching_service
from app.services.mentor_approval_service import mentor_approval_service

router = APIRouter(prefix="/mentors", tags=["AI Mentor Recommendations"])

@router.get("/recommendations", response_model=MentorRecommendationsResponse, status_code=status.HTTP_200_OK)
async def get_mentor_recommendations(
    limit: int = Query(10, ge=1, le=100, description="Pagination limit"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    skill: Optional[str] = Query(None, description="Optional skill filter"),
    career_goal: Optional[str] = Query(None, description="Optional career goal filter"),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve ranked mentor recommendations for the authenticated student using semantic matching."""
    return await matching_service.get_mentor_recommendations(
        student_id=current_user["id"],
        skill=skill,
        career_goal=career_goal,
        limit=limit,
        offset=offset,
    )

@router.post(
    "/{mentor_id}/approve",
    response_model=MentorApprovalResponse,
    status_code=status.HTTP_200_OK,
)
async def approve_mentor_recommendation(
    mentor_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Explicitly approve a specific mentor recommendation before creating a request.
    The approval is valid for 60 minutes and is consumed exactly once when the
    mentorship request is created. Callers can re-approve to refresh the window.
    """
    return await mentor_approval_service.approve(
        student_id=current_user["id"],
        mentor_id=mentor_id,
    )
