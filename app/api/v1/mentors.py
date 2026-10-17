from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user
from app.schemas.mentor import MentorRecommendationsResponse
from app.services.matching_service import matching_service

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
