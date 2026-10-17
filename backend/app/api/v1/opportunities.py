from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user
from app.schemas.opportunity import (
    OpportunitiesListResponse,
    OpportunityCreate,
    OpportunityResponse,
    OpportunityType,
)
from app.services.opportunity_service import opportunity_service

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])

@router.get("", response_model=OpportunitiesListResponse, status_code=status.HTTP_200_OK)
async def list_opportunities(
    type: Optional[OpportunityType] = Query(None, description="Filter by type (job, internship, collaboration, cofounder)"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Browse jobs, internships, collaborations, and cofounder opportunities."""
    return await opportunity_service.list_opportunities(opp_type=type, limit=limit, offset=offset)

@router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    opp: OpportunityCreate,
    current_user: dict = Depends(get_current_user),
):
    """Create a new opportunity (recruiters, founders, faculty, alumni)."""
    return await opportunity_service.create_opportunity(
        user_id=current_user["id"],
        user_role=current_user.get("role", "student"),
        data=opp,
    )
