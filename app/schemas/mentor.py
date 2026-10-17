from typing import List, Optional
from pydantic import BaseModel, Field

class MatchReason(BaseModel):
    code: str = Field(..., description="Machine-readable reason code")
    label: str = Field(..., description="Explainable description of match alignment")

class MentorRecommendationItem(BaseModel):
    mentor_id: str
    name: str
    current_role: str
    skills: List[str] = Field(default_factory=list)
    match_score: float = Field(..., ge=0.0, le=1.0, description="Normalized match score between 0.0 and 1.0")
    reasons: List[MatchReason] = Field(default_factory=list)
    profile_freshness: str = "current"
    can_request: bool = True

class MentorRecommendationsResponse(BaseModel):
    items: List[MentorRecommendationItem]
    algorithm_version: str = "v1"
    total: int
    limit: int
    offset: int
