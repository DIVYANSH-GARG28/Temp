import type {
  ApiErrorBody,
  Community,
  CurrentUser,
  FacultyRecommendation,
  FacultyRecommendationsResponse,
  KnowledgeGraphResponse,
  MeetingProposal,
  MentorshipRequest,
  MentorshipRequestListResponse,
  MentorshipRequestStatus,
  MentorApprovalResponse,
  MentorRecommendationFilters,
  MentorRecommendationsResponse,
  Notification,
  Opportunity,
  OpportunityType,
  ProfileMe,
  ProfileUpdateInput,
  ResearchProject,
  RegisterInput,
} from "../types/api";

const configuredApiBase = import.meta.env.VITE_API_BASE_URL?.trim();
const normalizedApiBase = configuredApiBase?.replace(/\/+$/, "");
const apiBase = configuredApiBase
  ? normalizedApiBase?.endsWith("/api/v1")
    ? normalizedApiBase
    : `${normalizedApiBase}/api/v1`
  : "/api/v1";
const authMode =
  import.meta.env.VITE_API_AUTH_MODE?.trim().toLowerCase() || "bearer";

if (authMode !== "bearer" && authMode !== "cookie") {
  throw new Error('VITE_API_AUTH_MODE must be "bearer" or "cookie".');
}

const TOKEN_STORAGE_KEY = "connected.access-token";
const TOKEN_EXPIRY_KEY = "connected.access-token-expiry";
const USER_STORAGE_KEY = "connected.cached-user";
export const SESSION_EXPIRED_EVENT = "connected:session-expired";

function getStorages(): Storage[] {
  const list: Storage[] = [];
  if (typeof window === "undefined") return list;
  try {
    list.push(window.localStorage);
  } catch {}
  try {
    list.push(window.sessionStorage);
  } catch {}
  return list;
}

function readStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  for (const storage of getStorages()) {
    try {
      const expiresAt = Number(storage.getItem(TOKEN_EXPIRY_KEY));
      const token = storage.getItem(TOKEN_STORAGE_KEY);
      if (token && expiresAt && expiresAt > Date.now()) {
        return token;
      }
      if (expiresAt && expiresAt <= Date.now()) {
        storage.removeItem(TOKEN_STORAGE_KEY);
        storage.removeItem(TOKEN_EXPIRY_KEY);
        storage.removeItem(USER_STORAGE_KEY);
      }
    } catch {}
  }
  return null;
}

let accessToken: string | null = readStoredAccessToken();

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly details?: unknown;

  constructor(
    message: string,
    status: number,
    code?: string,
    details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function setAccessToken(
  token: string | null,
  expiresIn?: number,
  user?: CurrentUser,
): void {
  accessToken = token;
  if (typeof window === "undefined") return;
  const storages = getStorages();
  if (!token || !expiresIn || !Number.isFinite(expiresIn) || expiresIn <= 0) {
    for (const storage of storages) {
      try {
        storage.removeItem(TOKEN_STORAGE_KEY);
        storage.removeItem(TOKEN_EXPIRY_KEY);
        storage.removeItem(USER_STORAGE_KEY);
      } catch {}
    }
    return;
  }
  const expiryValue = String(Date.now() + expiresIn * 1000);
  for (const storage of storages) {
    try {
      storage.setItem(TOKEN_STORAGE_KEY, token);
      storage.setItem(TOKEN_EXPIRY_KEY, expiryValue);
      if (user) {
        storage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
      }
    } catch {}
  }
}

export function getCachedUser(): CurrentUser | null {
  if (typeof window === "undefined") return null;
  for (const storage of getStorages()) {
    try {
      const raw = storage.getItem(USER_STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (isCurrentUser(parsed)) return parsed;
      }
    } catch {}
  }
  return null;
}

export function hasAccessToken(): boolean {
  accessToken = readStoredAccessToken();
  return Boolean(accessToken);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isUserRole(value: unknown): value is CurrentUser["role"] {
  return (
    typeof value === "string" &&
    ["student", "alumni", "faculty", "recruiter", "founder", "admin"].includes(
      value,
    )
  );
}

function isCurrentUser(value: unknown): value is CurrentUser {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.email === "string" &&
    isUserRole(value.role) &&
    typeof value.name === "string"
  );
}

function isProfileMe(value: unknown): value is ProfileMe {
  return (
    isRecord(value) &&
    typeof value.user_id === "string" &&
    isUserRole(value.role) &&
    typeof value.name === "string" &&
    Array.isArray(value.skills) &&
    value.skills.every((skill) => typeof skill === "string") &&
    ["career_goals", "research_interests", "interests"].every((field) =>
      value[field] === undefined ||
      (Array.isArray(value[field]) &&
        value[field].every((item: unknown) => typeof item === "string")),
    ) &&
    ["headline", "institution", "department", "degree", "current_organization",
      "current_role", "bio", "visibility", "verification_status",
      "profile_freshness", "updated_at", "profile_visibility"].every((field) =>
      value[field] === undefined ||
      value[field] === null ||
      typeof value[field] === "string",
    ) &&
    (value.graduation_year === undefined ||
      value.graduation_year === null ||
      typeof value.graduation_year === "number") &&
    (value.experience === undefined ||
      (Array.isArray(value.experience) && value.experience.every(isRecord))) &&
    (value.mentorship_preferences === undefined ||
      isRecord(value.mentorship_preferences))
  );
}

function isMentorshipRequest(value: unknown): value is MentorshipRequest {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.student_id === "string" &&
    typeof value.mentor_id === "string" &&
    typeof value.message === "string" &&
    typeof value.status === "string" &&
    ["pending", "accepted", "declined", "cancelled", "expired"].includes(
      value.status,
    ) &&
    typeof value.created_at === "string" &&
    typeof value.updated_at === "string" &&
    typeof value.deadline === "string" &&
    (value.response_at === undefined ||
      value.response_at === null ||
      typeof value.response_at === "string") &&
    (value.fallback_recommendation_id === undefined ||
      value.fallback_recommendation_id === null ||
      typeof value.fallback_recommendation_id === "string") &&
    (value.metadata === undefined || isRecord(value.metadata))
  );
}

function isPagedResponse<T>(
  value: unknown,
  isItem: (item: unknown) => item is T,
): value is { items: T[]; total: number; limit: number; offset: number } {
  return (
    isRecord(value) &&
    Array.isArray(value.items) &&
    value.items.every(isItem) &&
    typeof value.total === "number" &&
    typeof value.limit === "number" &&
    typeof value.offset === "number"
  );
}

function isFacultyRecommendation(value: unknown): value is FacultyRecommendation {
  return (
    isRecord(value) &&
    typeof value.faculty_id === "string" &&
    typeof value.name === "string" &&
    typeof value.department === "string" &&
    typeof value.institution === "string" &&
    Array.isArray(value.research_areas) &&
    value.research_areas.every((area) => typeof area === "string") &&
    typeof value.match_score === "number" &&
    Number.isFinite(value.match_score) &&
    value.match_score >= 0 &&
    value.match_score <= 1 &&
    typeof value.match_reason === "string" &&
    typeof value.active_projects_count === "number"
  );
}

function isGraphResponse(value: unknown): value is KnowledgeGraphResponse {
  return (
    isRecord(value) &&
    Array.isArray(value.nodes) &&
    value.nodes.every(
      (node) =>
        isRecord(node) &&
        typeof node.id === "string" &&
        typeof node.type === "string" &&
        typeof node.label === "string",
    ) &&
    Array.isArray(value.edges) &&
    value.edges.every(
      (edge) =>
        isRecord(edge) &&
        typeof edge.source === "string" &&
        typeof edge.target === "string" &&
        typeof edge.type === "string",
    )
  );
}

function isMentorApprovalResponse(
  value: unknown,
): value is MentorApprovalResponse {
  return (
    isRecord(value) &&
    typeof value.student_id === "string" &&
    typeof value.mentor_id === "string" &&
    typeof value.status === "string" &&
    typeof value.expires_at === "string" &&
    (value.message === undefined || typeof value.message === "string")
  );
}

function isOpportunity(value: unknown): value is Opportunity {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.creator_id === "string" &&
    typeof value.creator_role === "string" &&
    ["job", "internship", "collaboration", "cofounder"].includes(
      String(value.type),
    ) &&
    typeof value.title === "string" &&
    typeof value.description === "string" &&
    typeof value.organization === "string" &&
    (value.location === undefined || value.location === null || typeof value.location === "string") &&
    Array.isArray(value.required_skills) &&
    value.required_skills.every((skill) => typeof skill === "string") &&
    (value.deadline === undefined || value.deadline === null || typeof value.deadline === "string") &&
    (value.application_url === undefined || value.application_url === null || typeof value.application_url === "string") &&
    (value.contact_email === undefined || value.contact_email === null || typeof value.contact_email === "string") &&
    typeof value.is_active === "boolean" &&
    typeof value.created_at === "string"
  );
}

function isResearchProject(value: unknown): value is ResearchProject {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.faculty_id === "string" &&
    typeof value.faculty_name === "string" &&
    typeof value.title === "string" &&
    typeof value.description === "string" &&
    typeof value.research_area === "string" &&
    Array.isArray(value.required_skills) &&
    value.required_skills.every((skill) => typeof skill === "string") &&
    typeof value.availability === "string" &&
    typeof value.application_instructions === "string" &&
    typeof value.created_at === "string"
  );
}

function isNotification(value: unknown): value is Notification {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.user_id === "string" &&
    typeof value.title === "string" &&
    typeof value.message === "string" &&
    typeof value.type === "string" &&
    typeof value.read === "boolean" &&
    (value.link === undefined || value.link === null || typeof value.link === "string") &&
    typeof value.created_at === "string"
  );
}

function isCommunity(value: unknown): value is Community {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.name === "string" &&
    typeof value.description === "string" &&
    typeof value.category === "string" &&
    typeof value.member_count === "number" &&
    typeof value.is_private === "boolean" &&
    typeof value.created_at === "string"
  );
}

function isMeetingProposal(value: unknown): value is MeetingProposal {
  return (
    isRecord(value) &&
    typeof value.id === "string" &&
    typeof value.mentorship_request_id === "string" &&
    typeof value.proposer_id === "string" &&
    typeof value.proposed_time === "string" &&
    typeof value.timezone_str === "string" &&
    ["proposed", "accepted_by_one", "confirmed", "declined", "cancelled"].includes(
      String(value.status),
    ) &&
    isRecord(value.responses) &&
    Object.values(value.responses).every((response) => typeof response === "string") &&
    (value.note === undefined || value.note === null || typeof value.note === "string") &&
    typeof value.created_at === "string" &&
    typeof value.updated_at === "string"
  );
}

function isRecommendationResponse(
  value: unknown,
): value is MentorRecommendationsResponse {
  if (!isRecord(value) || !Array.isArray(value.items)) return false;
  if (
    typeof value.total !== "number" ||
    typeof value.limit !== "number" ||
    typeof value.offset !== "number"
  ) {
    return false;
  }

  return value.items.every(
    (item) =>
      isRecord(item) &&
      typeof item.mentor_id === "string" &&
      typeof item.name === "string" &&
      typeof item.current_role === "string" &&
      Array.isArray(item.skills) &&
      item.skills.every((skill) => typeof skill === "string") &&
      typeof item.match_score === "number" &&
      Number.isFinite(item.match_score) &&
      item.match_score >= 0 &&
      item.match_score <= 1 &&
      typeof item.can_request === "boolean" &&
      Array.isArray(item.reasons) &&
      item.reasons.every(
        (reason) =>
          isRecord(reason) &&
          typeof reason.code === "string" &&
          typeof reason.label === "string",
      ),
  );
}

function errorMessage(body: ApiErrorBody, status: number): string {
  if (body.error?.message) return body.error.message;
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    return body.detail
      .map((item) => {
        const location = item.loc?.join(".");
        return location ? `${location}: ${item.msg ?? "Invalid value"}` : item.msg;
      })
      .filter(Boolean)
      .join("; ");
  }
  return body.message || `The request failed (HTTP ${status}).`;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "application/json");

  if (authMode === "bearer" && accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  let response: Response;
  try {
    response = await fetch(`${apiBase}${path}`, {
      ...init,
      headers,
      credentials: authMode === "cookie" ? "include" : "same-origin",
    });
  } catch (error) {
    throw new ApiError(
      error instanceof Error
        ? `Could not reach the connectED API at ${apiBase}: ${error.message}. Please verify the FastAPI backend server is running on port 8000.`
        : `Could not reach the connectED API at ${apiBase}.`,
      0,
    );
  }

  if (response.status === 401 && accessToken) {
    setAccessToken(null);
    window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
  }

  if (response.status === 204) {
    if (!response.ok) {
      throw new ApiError("The request failed.", response.status);
    }
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const responseText = await response.text();
  let body: unknown = responseText;
  if (contentType.includes("application/json") && responseText) {
    try {
      body = JSON.parse(responseText) as unknown;
    } catch {
      throw new ApiError(
        `The API returned invalid JSON (HTTP ${response.status}).`,
        response.status,
      );
    }
  }

  if (!response.ok) {
    const errorBody =
      typeof body === "object" && body !== null
        ? (body as ApiErrorBody)
        : {};
    throw new ApiError(
      errorMessage(errorBody, response.status),
      response.status,
      errorBody.error?.code,
      errorBody.error?.details,
    );
  }

  return body as T;
}

export const api = {
  async register(input: RegisterInput): Promise<CurrentUser> {
    const data = await request<unknown>("/auth/register", {
      method: "POST",
      body: JSON.stringify(input),
    });
    if (
      !isRecord(data) ||
      typeof data.access_token !== "string" ||
      data.token_type !== "bearer" ||
      typeof data.expires_in !== "number" ||
      !Number.isFinite(data.expires_in) ||
      data.expires_in <= 0 ||
      !isCurrentUser(data.user)
    ) {
      throw new ApiError("The registration API returned an unexpected response.", 201);
    }
    setAccessToken(data.access_token, data.expires_in, data.user);
    return data.user;
  },

  async approveMentorRecommendation(
    mentorId: string,
  ): Promise<MentorApprovalResponse> {
    const data = await request<unknown>(
      `/mentors/${encodeURIComponent(mentorId)}/approve`,
      { method: "POST" },
    );
    if (!isMentorApprovalResponse(data)) {
      throw new ApiError("The mentor approval API returned an unexpected response.", 200);
    }
    return {
      ...data,
      message:
        typeof data.message === "string"
          ? data.message
          : "Mentor recommendation approved.",
    };
  },

  async login(email: string, password: string): Promise<CurrentUser> {
    const data = await request<unknown>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    if (
      !isRecord(data) ||
      typeof data.access_token !== "string" ||
      data.token_type !== "bearer" ||
      typeof data.expires_in !== "number" ||
      !Number.isFinite(data.expires_in) ||
      data.expires_in <= 0 ||
      !isCurrentUser(data.user)
    ) {
      throw new ApiError("The login API returned an unexpected response.", 200);
    }
    setAccessToken(data.access_token, data.expires_in, data.user);
    return data.user;
  },

  async getCurrentUser(): Promise<CurrentUser> {
    const data = await request<unknown>("/auth/me");
    if (!isCurrentUser(data)) {
      throw new ApiError("The current-user API returned an unexpected response.", 200);
    }
    for (const storage of getStorages()) {
      try {
        storage.setItem(USER_STORAGE_KEY, JSON.stringify(data));
      } catch {}
    }
    return data;
  },

  async logout(): Promise<void> {
    try {
      const data = await request<unknown>("/auth/logout", { method: "POST" });
      if (
        !isRecord(data) ||
        data.success !== true ||
        typeof data.message !== "string"
      ) {
        throw new ApiError("The logout API returned an unexpected response.", 200);
      }
    } finally {
      setAccessToken(null);
    }
  },

  async getMyProfile(): Promise<ProfileMe> {
    const data = await request<unknown>("/profiles/me");
    if (!isProfileMe(data)) {
      throw new ApiError("The profile API returned an unexpected response.", 200);
    }
    return data;
  },

  async updateMyProfile(input: ProfileUpdateInput): Promise<ProfileMe> {
    const data = await request<unknown>("/profiles/me", {
      method: "PATCH",
      body: JSON.stringify(input),
    });
    if (!isProfileMe(data)) {
      throw new ApiError("The profile API returned an unexpected response.", 200);
    }
    return data;
  },

  getMentorRecommendations(
    filters: MentorRecommendationFilters = {},
  ): Promise<MentorRecommendationsResponse> {
    const query = new URLSearchParams();
    if (filters.limit !== undefined) query.set("limit", String(filters.limit));
    if (filters.offset !== undefined) query.set("offset", String(filters.offset));
    if (filters.skill) query.set("skill", filters.skill);
    if (filters.career_goal) query.set("career_goal", filters.career_goal);
    const suffix = query.size > 0 ? `?${query.toString()}` : "";

    return request<unknown>(
      `/mentors/recommendations${suffix}`,
    ).then((data) => {
      if (!isRecommendationResponse(data)) {
        throw new ApiError(
          "The recommendations API returned an unexpected response.",
          200,
        );
      }

      return data;
    });
  },

  async getMentorshipRequests(filters: {
    status?: MentorshipRequestStatus;
    limit?: number;
    offset?: number;
  } = {}): Promise<MentorshipRequestListResponse> {
    const query = new URLSearchParams();
    if (filters.status) query.set("status", filters.status);
    if (filters.limit !== undefined) query.set("limit", String(filters.limit));
    if (filters.offset !== undefined) query.set("offset", String(filters.offset));
    const suffix = query.size > 0 ? `?${query.toString()}` : "";
    const data = await request<unknown>(`/mentorship-requests${suffix}`);
    if (!isPagedResponse(data, isMentorshipRequest)) {
      throw new ApiError("The mentorship requests API returned an unexpected response.", 200);
    }
    return data;
  },

  async getMentorshipRequest(requestId: string): Promise<MentorshipRequest> {
    const data = await request<unknown>(
      `/mentorship-requests/${encodeURIComponent(requestId)}`,
    );
    if (!isMentorshipRequest(data)) {
      throw new ApiError("The mentorship request API returned an unexpected response.", 200);
    }
    return data;
  },

  async getOpportunities(filters: {
    type?: OpportunityType;
    limit?: number;
    offset?: number;
  } = {}): Promise<{ items: Opportunity[]; total: number; limit: number; offset: number }> {
    const query = new URLSearchParams();
    if (filters.type) query.set("type", filters.type);
    if (filters.limit !== undefined) query.set("limit", String(filters.limit));
    if (filters.offset !== undefined) query.set("offset", String(filters.offset));
    const suffix = query.size ? `?${query.toString()}` : "";
    const data = await request<unknown>(`/opportunities${suffix}`);
    if (!isPagedResponse(data, isOpportunity)) {
      throw new ApiError("The opportunities API returned an unexpected response.", 200);
    }
    return data;
  },

  async getResearchProjects(filters: {
    research_area?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<{ items: ResearchProject[]; total: number; limit: number; offset: number }> {
    const query = new URLSearchParams();
    if (filters.research_area) query.set("research_area", filters.research_area);
    if (filters.limit !== undefined) query.set("limit", String(filters.limit));
    if (filters.offset !== undefined) query.set("offset", String(filters.offset));
    const suffix = query.size ? `?${query.toString()}` : "";
    const data = await request<unknown>(`/research-projects${suffix}`);
    if (!isPagedResponse(data, isResearchProject)) {
      throw new ApiError("The research projects API returned an unexpected response.", 200);
    }
    return data;
  },

  async getNotifications(filters: {
    limit?: number;
    offset?: number;
  } = {}): Promise<{ items: Notification[]; total: number; limit: number; offset: number }> {
    const query = new URLSearchParams();
    if (filters.limit !== undefined) query.set("limit", String(filters.limit));
    if (filters.offset !== undefined) query.set("offset", String(filters.offset));
    const suffix = query.size ? `?${query.toString()}` : "";
    const data = await request<unknown>(`/notifications${suffix}`);
    if (!isPagedResponse(data, isNotification)) {
      throw new ApiError("The notifications API returned an unexpected response.", 200);
    }
    return data;
  },

  async getCommunities(filters: {
    limit?: number;
    offset?: number;
  } = {}): Promise<{ items: Community[]; total: number; limit: number; offset: number }> {
    const query = new URLSearchParams();
    if (filters.limit !== undefined) query.set("limit", String(filters.limit));
    if (filters.offset !== undefined) query.set("offset", String(filters.offset));
    const suffix = query.size ? `?${query.toString()}` : "";
    const data = await request<unknown>(`/communities${suffix}`);
    if (!isPagedResponse(data, isCommunity)) {
      throw new ApiError("The communities API returned an unexpected response.", 200);
    }
    return data;
  },

  async getMeetingProposals(
    requestId: string,
  ): Promise<{ items: MeetingProposal[]; total: number }> {
    const data = await request<unknown>(
      `/mentorship-requests/${encodeURIComponent(requestId)}/meeting-proposals`,
    );
    if (
      !isRecord(data) ||
      !Array.isArray(data.items) ||
      !data.items.every(isMeetingProposal) ||
      typeof data.total !== "number"
    ) {
      throw new ApiError("The meeting proposals API returned an unexpected response.", 200);
    }
    return data as { items: MeetingProposal[]; total: number };
  },

  async createMeetingProposal(
    requestId: string,
    input: { proposed_time: string; timezone_str: string; note?: string },
  ): Promise<MeetingProposal> {
    const data = await request<unknown>(
      `/mentorship-requests/${encodeURIComponent(requestId)}/meeting-proposals`,
      { method: "POST", body: JSON.stringify(input) },
    );
    if (!isMeetingProposal(data)) {
      throw new ApiError("The meeting proposal API returned an unexpected response.", 201);
    }
    return data;
  },

  async respondToMeetingProposal(
    proposalId: string,
    input: { action: "accept" | "decline"; note?: string },
  ): Promise<MeetingProposal> {
    const data = await request<unknown>(
      `/meeting-proposals/${encodeURIComponent(proposalId)}/respond`,
      { method: "POST", body: JSON.stringify(input) },
    );
    if (!isMeetingProposal(data)) {
      throw new ApiError("The meeting response API returned an unexpected response.", 200);
    }
    return data;
  },

  async createMentorshipRequest(input: {
    mentor_id: string;
    message: string;
  }): Promise<MentorshipRequest> {
    const data = await request<unknown>("/mentorship-requests", {
      method: "POST",
      body: JSON.stringify(input),
    });
    if (!isMentorshipRequest(data)) {
      throw new ApiError("The mentorship request API returned an unexpected response.", 201);
    }
    return data;
  },

  async cancelMentorshipRequest(requestId: string): Promise<{
    id: string;
    status: "cancelled";
    message: string;
    updated_at: string;
  }> {
    const data = await request<unknown>(
      `/mentorship-requests/${encodeURIComponent(requestId)}/cancel`,
      { method: "POST" },
    );
    if (
      !isRecord(data) ||
      typeof data.id !== "string" ||
      data.status !== "cancelled" ||
      typeof data.message !== "string" ||
      typeof data.updated_at !== "string"
    ) {
      throw new ApiError("The cancellation API returned an unexpected response.", 200);
    }
    return {
      id: data.id,
      status: "cancelled",
      message: data.message,
      updated_at: data.updated_at,
    };
  },

  async getFacultyRecommendations(): Promise<FacultyRecommendationsResponse> {
    const data = await request<unknown>("/faculty/recommendations");
    if (!isPagedResponse(data, isFacultyRecommendation)) {
      throw new ApiError("The faculty recommendations API returned an unexpected response.", 200);
    }
    return data;
  },

  async getKnowledgeGraph(): Promise<KnowledgeGraphResponse> {
    const data = await request<unknown>("/graph/me");
    if (!isGraphResponse(data)) {
      throw new ApiError("The knowledge graph API returned an unexpected response.", 200);
    }
    return data;
  },
};
