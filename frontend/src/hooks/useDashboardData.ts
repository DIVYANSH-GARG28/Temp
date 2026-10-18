import { useCallback, useEffect, useState } from "react";
import { ApiError, api } from "../services/api";
import type {
  Community,
  FacultyRecommendationsResponse,
  KnowledgeGraphResponse,
  MeetingProposal,
  MentorshipRequestListResponse,
  Notification,
  Opportunity,
  ProfileMe,
  ResearchProject,
} from "../types/api";

function errorText(error: unknown, fallback: string): string {
  return error instanceof ApiError || error instanceof Error
    ? error.message
    : fallback;
}

export function useDashboardData() {
  const [profile, setProfile] = useState<ProfileMe | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState("");
  const [requests, setRequests] = useState<MentorshipRequestListResponse | null>(
    null,
  );
  const [pendingTotal, setPendingTotal] = useState<number | null>(null);
  const [acceptedTotal, setAcceptedTotal] = useState<number | null>(null);
  const [requestsLoading, setRequestsLoading] = useState(true);
  const [requestsError, setRequestsError] = useState("");
  const [faculty, setFaculty] =
    useState<FacultyRecommendationsResponse | null>(null);
  const [facultyLoading, setFacultyLoading] = useState(true);
  const [facultyError, setFacultyError] = useState("");
  const [graph, setGraph] = useState<KnowledgeGraphResponse | null>(null);
  const [graphLoading, setGraphLoading] = useState(true);
  const [graphError, setGraphError] = useState("");
  const [opportunities, setOpportunities] = useState<Opportunity[] | null>(null);
  const [opportunitiesLoading, setOpportunitiesLoading] = useState(true);
  const [opportunitiesError, setOpportunitiesError] = useState("");
  const [researchProjects, setResearchProjects] = useState<ResearchProject[] | null>(null);
  const [researchLoading, setResearchLoading] = useState(true);
  const [researchError, setResearchError] = useState("");
  const [notifications, setNotifications] = useState<Notification[] | null>(null);
  const [notificationsLoading, setNotificationsLoading] = useState(true);
  const [notificationsError, setNotificationsError] = useState("");
  const [communities, setCommunities] = useState<Community[] | null>(null);
  const [communitiesLoading, setCommunitiesLoading] = useState(true);
  const [communitiesError, setCommunitiesError] = useState("");
  const [meetingProposals, setMeetingProposals] = useState<MeetingProposal[]>([]);
  const [meetingsLoading, setMeetingsLoading] = useState(false);
  const [meetingsError, setMeetingsError] = useState("");
  const [cancellingRequestId, setCancellingRequestId] = useState<string | null>(
    null,
  );
  const [requestActionMessage, setRequestActionMessage] = useState("");
  const [requestActionError, setRequestActionError] = useState("");

  const loadProfile = useCallback(async () => {
    setProfileLoading(true);
    setProfileError("");
    try {
      setProfile(await api.getMyProfile());
    } catch (error) {
      setProfile(null);
      setProfileError(errorText(error, "Could not load your profile."));
    } finally {
      setProfileLoading(false);
    }
  }, []);

  const loadRequests = useCallback(async () => {
    setRequestsLoading(true);
    setRequestsError("");
    const [recentResult, pendingResult, acceptedResult] = await Promise.allSettled([
      api.getMentorshipRequests({ limit: 5, offset: 0 }),
      api.getMentorshipRequests({ status: "pending", limit: 1, offset: 0 }),
      api.getMentorshipRequests({ status: "accepted", limit: 1, offset: 0 }),
    ]);

    if (recentResult.status === "fulfilled") {
      setRequests(recentResult.value);
    } else {
      setRequests(null);
      setRequestsError(
        errorText(recentResult.reason, "Could not load mentorship requests."),
      );
    }
    setPendingTotal(
      pendingResult.status === "fulfilled" ? pendingResult.value.total : null,
    );
    setAcceptedTotal(
      acceptedResult.status === "fulfilled" ? acceptedResult.value.total : null,
    );
    if (pendingResult.status === "rejected" || acceptedResult.status === "rejected") {
      setRequestsError((current) =>
        current || "Request status totals could not be loaded.",
      );
    }
    setRequestsLoading(false);
  }, []);

  const loadFaculty = useCallback(async () => {
    setFacultyLoading(true);
    setFacultyError("");
    try {
      setFaculty(await api.getFacultyRecommendations());
    } catch (error) {
      setFaculty(null);
      setFacultyError(errorText(error, "Could not load faculty recommendations."));
    } finally {
      setFacultyLoading(false);
    }
  }, []);

  const loadGraph = useCallback(async () => {
    setGraphLoading(true);
    setGraphError("");
    try {
      setGraph(await api.getKnowledgeGraph());
    } catch (error) {
      setGraph(null);
      setGraphError(errorText(error, "Could not load your knowledge graph."));
    } finally {
      setGraphLoading(false);
    }
  }, []);

  const loadOpportunities = useCallback(async () => {
    setOpportunitiesLoading(true);
    setOpportunitiesError("");
    try {
      const response = await api.getOpportunities({ limit: 5, offset: 0 });
      setOpportunities(response.items);
    } catch (error) {
      setOpportunities(null);
      setOpportunitiesError(errorText(error, "Could not load opportunities."));
    } finally {
      setOpportunitiesLoading(false);
    }
  }, []);

  const loadResearchProjects = useCallback(async () => {
    setResearchLoading(true);
    setResearchError("");
    try {
      const response = await api.getResearchProjects({ limit: 5, offset: 0 });
      setResearchProjects(response.items);
    } catch (error) {
      setResearchProjects(null);
      setResearchError(errorText(error, "Could not load research projects."));
    } finally {
      setResearchLoading(false);
    }
  }, []);

  const loadNotifications = useCallback(async () => {
    setNotificationsLoading(true);
    setNotificationsError("");
    try {
      const response = await api.getNotifications({ limit: 5, offset: 0 });
      setNotifications(response.items);
    } catch (error) {
      setNotifications(null);
      setNotificationsError(errorText(error, "Could not load notifications."));
    } finally {
      setNotificationsLoading(false);
    }
  }, []);

  const loadCommunities = useCallback(async () => {
    setCommunitiesLoading(true);
    setCommunitiesError("");
    try {
      const response = await api.getCommunities({ limit: 5, offset: 0 });
      setCommunities(response.items);
    } catch (error) {
      setCommunities(null);
      setCommunitiesError(errorText(error, "Could not load communities."));
    } finally {
      setCommunitiesLoading(false);
    }
  }, []);

  const loadMeetings = useCallback(async (acceptedRequests: MentorshipRequestListResponse["items"]) => {
    if (acceptedRequests.length === 0) {
      setMeetingProposals([]);
      setMeetingsError("");
      setMeetingsLoading(false);
      return;
    }
    setMeetingsLoading(true);
    setMeetingsError("");
    const results = await Promise.allSettled(
      acceptedRequests.map((request) => api.getMeetingProposals(request.id)),
    );
    const failures = results.filter((result) => result.status === "rejected");
    if (failures.length > 0) {
      setMeetingProposals(
        results.flatMap((result) =>
          result.status === "fulfilled" ? result.value.items : [],
        ),
      );
      setMeetingsError("Some meeting proposals could not be loaded.");
    } else {
      setMeetingProposals(
        results.flatMap((result) =>
          result.status === "fulfilled" ? result.value.items : [],
        ),
      );
    }
    setMeetingsLoading(false);
  }, []);

  useEffect(() => {
    void loadProfile();
    void loadRequests();
    void loadFaculty();
    void loadGraph();
    void loadOpportunities();
    void loadResearchProjects();
    void loadNotifications();
    void loadCommunities();
  }, [
    loadCommunities,
    loadFaculty,
    loadGraph,
    loadNotifications,
    loadOpportunities,
    loadProfile,
    loadRequests,
    loadResearchProjects,
  ]);

  useEffect(() => {
    const acceptedRequests =
      requests?.items.filter((request) => request.status === "accepted") ?? [];
    void loadMeetings(acceptedRequests);
  }, [loadMeetings, requests]);

  const cancelRequest = useCallback(
    async (requestId: string) => {
      setCancellingRequestId(requestId);
      setRequestActionMessage("");
      setRequestActionError("");
      try {
        const response = await api.cancelMentorshipRequest(requestId);
        setRequestActionMessage(response.message);
        await loadRequests();
      } catch (error) {
        setRequestActionError(
          errorText(error, "The request could not be cancelled."),
        );
      } finally {
        setCancellingRequestId(null);
      }
    },
    [loadRequests],
  );

  return {
    profile,
    profileLoading,
    profileError,
    loadProfile,
    requests,
    pendingTotal,
    acceptedTotal,
    requestsLoading,
    requestsError,
    loadRequests,
    cancelRequest,
    cancellingRequestId,
    requestActionMessage,
    requestActionError,
    loadMeetings,
    meetingProposals,
    meetingsLoading,
    meetingsError,
    faculty,
    facultyLoading,
    facultyError,
    loadFaculty,
    graph,
    graphLoading,
    graphError,
    loadGraph,
    opportunities,
    opportunitiesLoading,
    opportunitiesError,
    loadOpportunities,
    researchProjects,
    researchLoading,
    researchError,
    loadResearchProjects,
    notifications,
    notificationsLoading,
    notificationsError,
    loadNotifications,
    communities,
    communitiesLoading,
    communitiesError,
    loadCommunities,
  };
}
