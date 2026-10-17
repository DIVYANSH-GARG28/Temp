from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MentorshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class MentorshipRequestCreate(BaseModel):
    mentor_id: str = Field(..., description="Target mentor (alumni) user ID")
    message: str = Field(..., min_length=10, max_length=1500, description="Message stating mentorship goals and context")

class MentorshipRequestResponse(BaseModel):
    id: str
    student_id: str
    mentor_id: str
    message: str
    status: MentorshipStatus
    created_at: datetime
    updated_at: datetime
    deadline: datetime
    response_at: Optional[datetime] = None
    fallback_recommendation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MentorshipRequestCancelResponse(BaseModel):
    id: str
    status: MentorshipStatus = MentorshipStatus.CANCELLED
    message: str = "Mentorship request cancelled successfully."
    updated_at: datetime

class MentorshipRequestsListResponse(BaseModel):
    items: List[MentorshipRequestResponse]
    total: int
    limit: int
    offset: int
