from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class CommunityResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    member_count: int = 0
    is_private: bool = False
    created_at: datetime

class CommunitiesListResponse(BaseModel):
    items: List[CommunityResponse]
    total: int
    limit: int
    offset: int

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str  # mentorship_request, meeting_proposal, fallback_recommendation, system
    read: bool = False
    link: Optional[str] = None
    created_at: datetime

class NotificationsListResponse(BaseModel):
    items: List[NotificationResponse]
    total: int
    limit: int
    offset: int
