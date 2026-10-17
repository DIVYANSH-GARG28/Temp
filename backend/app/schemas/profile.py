from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import UserRole

class ProfileVisibility(str, Enum):
    PUBLIC = "public"
    INSTITUTION_ONLY = "institution_only"
    PRIVATE = "private"

class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    FLAGGED = "flagged"

class MentorshipPreferences(BaseModel):
    accepting_requests: bool = True
    max_mentees: int = 5
    preferred_topics: List[str] = Field(default_factory=list)
    preferred_communication: str = "Telegram"

class ProfileMeResponse(BaseModel):
    user_id: str
    role: UserRole
    name: str
    headline: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    current_organization: Optional[str] = None
    current_role: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    career_goals: List[str] = Field(default_factory=list)
    bio: Optional[str] = None
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    research_interests: List[str] = Field(default_factory=list)
    mentorship_preferences: MentorshipPreferences = Field(default_factory=MentorshipPreferences)
    visibility: ProfileVisibility = ProfileVisibility.PUBLIC
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    profile_freshness: str = "current"
    updated_at: datetime

class ProfilePatchRequest(BaseModel):
    headline: Optional[str] = Field(None, max_length=150)
    institution: Optional[str] = Field(None, max_length=120)
    department: Optional[str] = Field(None, max_length=120)
    degree: Optional[str] = Field(None, max_length=120)
    graduation_year: Optional[int] = None
    current_organization: Optional[str] = Field(None, max_length=150)
    current_role: Optional[str] = Field(None, max_length=150)
    skills: Optional[List[str]] = None
    career_goals: Optional[List[str]] = None
    bio: Optional[str] = Field(None, max_length=2000)
    experience: Optional[List[Dict[str, Any]]] = None
    research_interests: Optional[List[str]] = None
    mentorship_preferences: Optional[MentorshipPreferences] = None
    visibility: Optional[ProfileVisibility] = None

class StudentProfileResponse(BaseModel):
    user_id: str
    name: str
    headline: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: List[str] = Field(default_factory=list)
    career_goals: List[str] = Field(default_factory=list)
    bio: Optional[str] = None
    research_interests: List[str] = Field(default_factory=list)
    visibility: ProfileVisibility
    updated_at: datetime

class AlumniProfileResponse(BaseModel):
    user_id: str
    name: str
    headline: Optional[str] = None
    institution: Optional[str] = None
    degree: Optional[str] = None
    graduation_year: Optional[int] = None
    current_organization: Optional[str] = None
    current_role: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    bio: Optional[str] = None
    mentorship_preferences: MentorshipPreferences
    visibility: ProfileVisibility
    verification_status: VerificationStatus
    profile_freshness: str
    updated_at: datetime

class AlumniVerificationResponse(BaseModel):
    user_id: str
    name: str
    verification_status: VerificationStatus
    verified_at: Optional[datetime] = None
    evidence_source: Optional[str] = None
    freshness_score: float = 1.0
    profile_freshness: str = "current"
    last_verified_by: Optional[str] = None
    notes: Optional[str] = None
