from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class MeetingStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED_BY_ONE = "accepted_by_one"
    CONFIRMED = "confirmed"
    DECLINED = "declined"
    CANCELLED = "cancelled"

class ProposalResponseAction(str, Enum):
    ACCEPT = "accept"
    DECLINE = "decline"

class MeetingProposalCreate(BaseModel):
    proposed_time: datetime = Field(..., description="Proposed meeting time in UTC or with timezone offset")
    timezone_str: str = Field(default="UTC", description="Timezone of proposal, e.g. America/New_York or Asia/Kolkata")
    note: Optional[str] = Field(None, max_length=500, description="Optional note or meeting agenda")

class MeetingProposalRespond(BaseModel):
    action: ProposalResponseAction = Field(..., description="'accept' or 'decline'")
    note: Optional[str] = Field(None, max_length=500)

class MeetingProposalResponse(BaseModel):
    id: str
    mentorship_request_id: str
    proposer_id: str
    proposed_time: datetime
    timezone_str: str
    status: MeetingStatus
    responses: Dict[str, str] = Field(
        default_factory=dict,
        description="Map of participant_id -> response ('accepted' or 'declined')",
    )
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class MeetingProposalsListResponse(BaseModel):
    items: List[MeetingProposalResponse]
    total: int
