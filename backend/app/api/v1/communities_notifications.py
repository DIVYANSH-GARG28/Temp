from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user
from app.schemas.community import (
    CommunitiesListResponse,
    NotificationsListResponse,
)
from app.services.notification_service import notification_service

router = APIRouter(tags=["Communities and Notifications"])

@router.get("/communities", response_model=CommunitiesListResponse, status_code=status.HTTP_200_OK)
async def list_communities(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """List discoverable communities."""
    return await notification_service.list_communities(limit=limit, offset=offset)

@router.get("/notifications", response_model=NotificationsListResponse, status_code=status.HTTP_200_OK)
async def list_notifications(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """List notifications for the current authenticated user."""
    return await notification_service.list_notifications(
        user_id=current_user["id"],
        limit=limit,
        offset=offset,
    )
