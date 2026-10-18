export type UserRole =
  | "student"
  | "alumni"
  | "faculty"
  | "recruiter"
  | "founder"
  | "admin";

export interface CurrentUser {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active?: boolean;
  telegram_linked?: boolean;
  created_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: CurrentUser;
}

export interface RegisterInput {
  email: string;
  password: string;
  role: "student" | "alumni";
  name: string;
}

export interface ProfileMe {
  user_id: string;
  role: UserRole;
  name: string;
  headline?: string | null;
  institution?: string | null;
  department?: string | null;
  degree?: string | null;
  graduation_year?: number | null;
  current_organization?: string | null;
  current_role?: string | null;
  skills: string[];
  career_goals?: string[];
  research_interests?: string[];
  interests?: string[];
  bio?: string | null;
  mentorship_preferences?: {
    accepting_requests?: boolean;
    max_mentees?: number;
    preferred_topics?: string[];
    preferred_communication?: string;
  };
  visibility?: "public" | "institution_only" | "private";
  verification_status?: "unverified" | "pending" | "verified" | "flagged";
  profile_freshness?: string;
  updated_at?: string;
  profile_visibility?: string;
}

export interface ProfileUpdateInput {
  headline?: string;
  institution?: string;
  department?: string;
  degree?: string;
  graduation_year?: number;
  current_organization?: string;
  current_role?: string;
  skills?: string[];
  career_goals?: string[];
  bio?: string;
  experience?: Array<Record<string, unknown>>;
  research_interests?: string[];
  visibility?: "public" | "institution_only" | "private";
}

export type ProfileFreshness = "current" | "stale" | "unknown" | string;

export interface MatchReason {
  code: string;
  label: string;
}

export interface MentorRecommendation {
  mentor_id: string;
  name: string;
  current_role: string;
  skills: string[];
  match_score: number;
  reasons: MatchReason[];
  profile_freshness?: ProfileFreshness;
  can_request: boolean;
}

export interface MentorRecommendationsResponse {
  items: MentorRecommendation[];
  algorithm_version?: string;
  total: number;
  limit: number;
  offset: number;
}

export interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
    details?: unknown;
  };
  detail?: string | Array<{ msg?: string; loc?: Array<string | number> }>;
  message?: string;
}

export interface MentorRecommendationFilters {
  limit?: number;
  offset?: number;
  skill?: string;
  career_goal?: string;
}

export type MentorshipRequestStatus =
  | "pending"
  | "accepted"
  | "declined"
  | "cancelled"
  | "expired";

export interface MentorshipRequest {
  id: string;
  student_id: string;
  mentor_id: string;
  message: string;
  status: MentorshipRequestStatus;
  created_at: string;
  updated_at: string;
  deadline: string;
  response_at?: string | null;
  fallback_recommendation_id?: string | null;
  metadata?: Record<string, unknown>;
}

export interface MentorshipRequestListResponse {
  items: MentorshipRequest[];
  total: number;
  limit: number;
  offset: number;
}

export interface FacultyRecommendation {
  faculty_id: string;
  name: string;
  department: string;
  institution: string;
  research_areas: string[];
  match_score: number;
  match_reason: string;
  active_projects_count: number;
}

export interface FacultyRecommendationsResponse {
  items: FacultyRecommendation[];
  total: number;
  limit: number;
  offset: number;
}

export interface KnowledgeGraphNode {
  id: string;
  type: string;
  label: string;
  properties?: Record<string, unknown>;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  type: string;
  properties?: Record<string, unknown>;
}

export interface KnowledgeGraphResponse {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

export interface MentorApprovalResponse {
  student_id: string;
  mentor_id: string;
  status: string;
  expires_at: string;
  message: string;
}

export type OpportunityType = "job" | "internship" | "collaboration" | "cofounder";

export interface Opportunity {
  id: string;
  creator_id: string;
  creator_role: string;
  type: OpportunityType;
  title: string;
  description: string;
  organization: string;
  location?: string | null;
  required_skills: string[];
  deadline?: string | null;
  application_url?: string | null;
  contact_email?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface ResearchProject {
  id: string;
  faculty_id: string;
  faculty_name: string;
  title: string;
  description: string;
  research_area: string;
  required_skills: string[];
  availability: "open" | "closed" | "review" | string;
  application_instructions: string;
  created_at: string;
}

export interface Notification {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: string;
  read: boolean;
  link?: string | null;
  created_at: string;
}

export interface Community {
  id: string;
  name: string;
  description: string;
  category: string;
  member_count: number;
  is_private: boolean;
  created_at: string;
}

export type MeetingStatus =
  | "proposed"
  | "accepted_by_one"
  | "confirmed"
  | "declined"
  | "cancelled";

export interface MeetingProposal {
  id: string;
  mentorship_request_id: string;
  proposer_id: string;
  proposed_time: string;
  timezone_str: string;
  status: MeetingStatus;
  responses: Record<string, string>;
  note?: string | null;
  created_at: string;
  updated_at: string;
}
