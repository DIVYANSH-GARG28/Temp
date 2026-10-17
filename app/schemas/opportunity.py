from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class OpportunityType(str, Enum):
    JOB = "job"
    INTERNSHIP = "internship"
    COLLABORATION = "collaboration"
    COFOUNDER = "cofounder"

class OpportunityCreate(BaseModel):
    type: OpportunityType = Field(..., description="Allowed types: job, internship, collaboration, cofounder")
    title: str = Field(..., min_length=3, max_length=150)
    description: str = Field(..., min_length=10, max_length=5000)
    organization: str = Field(..., min_length=2, max_length=150)
    location: Optional[str] = Field("Remote", max_length=100)
    required_skills: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    application_url: Optional[str] = None
    contact_email: Optional[str] = None

class OpportunityResponse(BaseModel):
    id: str
    creator_id: str
    creator_role: str
    type: OpportunityType
    title: str
    description: str
    organization: str
    location: Optional[str] = "Remote"
    required_skills: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    application_url: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool = True
    created_at: datetime

class OpportunitiesListResponse(BaseModel):
    items: List[OpportunityResponse]
    total: int
    limit: int
    offset: int
