from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class FacultyRecommendationItem(BaseModel):
    faculty_id: str
    name: str
    department: str
    institution: str
    research_areas: List[str] = Field(default_factory=list)
    match_score: float = Field(..., ge=0.0, le=1.0)
    match_reason: str
    active_projects_count: int = 0

class FacultyRecommendationsResponse(BaseModel):
    items: List[FacultyRecommendationItem]
    total: int
    limit: int
    offset: int

class ResearchProjectResponse(BaseModel):
    id: str
    faculty_id: str
    faculty_name: str
    title: str
    description: str
    research_area: str
    required_skills: List[str] = Field(default_factory=list)
    availability: str = "open"  # open, closed, review
    application_instructions: str
    created_at: datetime

class ResearchProjectsListResponse(BaseModel):
    items: List[ResearchProjectResponse]
    total: int
    limit: int
    offset: int
