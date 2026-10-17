from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user
from app.schemas.research import (
    FacultyRecommendationsResponse,
    ResearchProjectsListResponse,
)
from app.services.research_service import research_service

router = APIRouter(tags=["Faculty and Research Projects"])

@router.get("/faculty/recommendations", response_model=FacultyRecommendationsResponse, status_code=status.HTTP_200_OK)
async def get_faculty_recommendations(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve ranked faculty recommendations for the authenticated student."""
    return await research_service.get_faculty_recommendations(
        student_id=current_user["id"],
        limit=limit,
        offset=offset,
    )

@router.get("/research-projects", response_model=ResearchProjectsListResponse, status_code=status.HTTP_200_OK)
async def list_research_projects(
    research_area: Optional[str] = Query(None, description="Optional research area filter"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Browse active research projects."""
    return await research_service.list_projects(
        research_area=research_area,
        limit=limit,
        offset=offset,
    )
