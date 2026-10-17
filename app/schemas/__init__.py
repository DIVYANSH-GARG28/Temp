from app.schemas.common import UserRole, ErrorDetail, StandardErrorResponse, PaginatedResponse
from app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
    LogoutResponse,
)
from app.schemas.profile import (
    ProfileMeResponse,
    ProfilePatchRequest,
    StudentProfileResponse,
    AlumniProfileResponse,
    AlumniVerificationResponse,
    ProfileVisibility,
    VerificationStatus,
)
from app.schemas.mentor import (
    MatchReason,
    MentorRecommendationItem,
    MentorRecommendationsResponse,
)
from app.schemas.mentorship import (
    MentorshipStatus,
    MentorshipRequestCreate,
    MentorshipRequestResponse,
    MentorshipRequestCancelResponse,
    MentorshipRequestsListResponse,
)
from app.schemas.meeting import (
    MeetingStatus,
    ProposalResponseAction,
    MeetingProposalCreate,
    MeetingProposalRespond,
    MeetingProposalResponse,
    MeetingProposalsListResponse,
)
from app.schemas.telegram import (
    TelegramLinkInitiateResponse,
    TelegramWebhookUpdate,
    TelegramWebhookResponse,
)
from app.schemas.research import (
    FacultyRecommendationItem,
    FacultyRecommendationsResponse,
    ResearchProjectResponse,
    ResearchProjectsListResponse,
)
from app.schemas.opportunity import (
    OpportunityType,
    OpportunityCreate,
    OpportunityResponse,
    OpportunitiesListResponse,
)
from app.schemas.graph import GraphNode, GraphEdge, GraphResponse
from app.schemas.community import (
    CommunityResponse,
    CommunitiesListResponse,
    NotificationResponse,
    NotificationsListResponse,
)
