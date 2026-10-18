import {
  ArrowRight,
  ArrowUpRight,
  BriefcaseBusiness,
  CalendarClock,
  CheckCircle2,
  Compass,
  GraduationCap,
  MessageCircle,
  Network,
  Pencil,
  Sparkles,
  UsersRound,
  X,
} from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { MentorCard } from "../components/MentorCard";
import { RetryButton, StatusView } from "../components/StatusView";
import { ApiError, api } from "../services/api";
import { useDashboardData } from "../hooks/useDashboardData";
import type {
  CurrentUser,
  MentorRecommendation,
  MentorRecommendationsResponse,
} from "../types/api";

const summaryItems = [
  {
    label: "Mentor recommendations",
    detail: "Live total from the matching service",
    icon: Sparkles,
    metric: "recommendations",
  },
  {
    label: "Pending requests",
    detail: "Server total · awaiting mentor response",
    icon: MessageCircle,
    metric: "pending",
  },
  {
    label: "Accepted requests",
    detail: "Server total · mentorship accepted",
    icon: CheckCircle2,
    metric: "accepted",
  },
  {
    label: "Relevant opportunities",
    detail: "Live total from the opportunity service",
    icon: BriefcaseBusiness,
    metric: "opportunities",
  },
] as const;

function formatDate(value: string | null | undefined): string | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toLocaleString();
}

function safeExternalUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : null;
  } catch {
    return null;
  }
}

export function DashboardPage() {
  const supportingData = useDashboardData();
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [recommendations, setRecommendations] =
    useState<MentorRecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [userError, setUserError] = useState<ApiError | null>(null);
  const [selectedMentor, setSelectedMentor] =
    useState<MentorRecommendation | null>(null);
  const [requestMessage, setRequestMessage] = useState("");
  const [requestMessageError, setRequestMessageError] = useState("");
  const [sendingRequest, setSendingRequest] = useState(false);
  const [requestSuccess, setRequestSuccess] = useState("");
  const [requestError, setRequestError] = useState("");
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileHeadline, setProfileHeadline] = useState("");
  const [profileSkills, setProfileSkills] = useState("");
  const [profileBio, setProfileBio] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileActionMessage, setProfileActionMessage] = useState("");
  const [profileActionError, setProfileActionError] = useState("");
  const [viewingRequestId, setViewingRequestId] = useState<string | null>(null);
  const [viewingRequest, setViewingRequest] =
    useState<Awaited<ReturnType<typeof api.getMentorshipRequest>> | null>(null);
  const [requestDetailLoading, setRequestDetailLoading] = useState(false);
  const [requestDetailError, setRequestDetailError] = useState("");
  const requestDetailSequence = useRef(0);
  const [meetingDraftRequestId, setMeetingDraftRequestId] = useState<string | null>(null);
  const [meetingDraftTime, setMeetingDraftTime] = useState("");
  const [meetingDraftNote, setMeetingDraftNote] = useState("");
  const [meetingActionBusy, setMeetingActionBusy] = useState(false);
  const [meetingActionMessage, setMeetingActionMessage] = useState("");
  const [meetingActionError, setMeetingActionError] = useState("");

  async function submitMeetingProposal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!meetingDraftRequestId || !meetingDraftTime || meetingActionBusy) return;
    setMeetingActionBusy(true);
    setMeetingActionError("");
    setMeetingActionMessage("");
    try {
      await api.createMeetingProposal(meetingDraftRequestId, {
        proposed_time: new Date(meetingDraftTime).toISOString(),
        timezone_str:
          Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC",
        note: meetingDraftNote.trim() || undefined,
      });
      setMeetingActionMessage("Meeting time proposed. Your mentor will be notified.");
      setMeetingDraftRequestId(null);
      setMeetingDraftTime("");
      setMeetingDraftNote("");
      await supportingData.loadRequests();
    } catch (cause) {
      setMeetingActionError(
        cause instanceof ApiError
          ? cause.message
          : "The meeting time could not be proposed.",
      );
    } finally {
      setMeetingActionBusy(false);
    }
  }

  async function respondToMeeting(proposalId: string, action: "accept" | "decline") {
    if (meetingActionBusy) return;
    setMeetingActionBusy(true);
    setMeetingActionError("");
    setMeetingActionMessage("");
    try {
      await api.respondToMeetingProposal(proposalId, { action });
      setMeetingActionMessage(
        action === "accept"
          ? "Your response was recorded. A meeting is confirmed only when both people accept."
          : "You declined this proposed meeting time.",
      );
      await supportingData.loadRequests();
    } catch (cause) {
      setMeetingActionError(
        cause instanceof ApiError
          ? cause.message
          : "Your meeting response could not be saved.",
      );
    } finally {
      setMeetingActionBusy(false);
    }
  }

  useEffect(() => {
    let active = true;

    void api.getCurrentUser().then(
      (currentUser) => {
        if (!active) return;
        setUser(currentUser);
        if (currentUser.role === "student") {
          void loadRecommendations();
        } else {
          setLoading(false);
        }
      },
      (cause: unknown) => {
        if (active) {
          setUser(null);
          setUserError(
            cause instanceof ApiError
              ? cause
              : new ApiError("Could not load your account profile.", 0),
          );
          setLoading(false);
        }
      },
    );

    return () => {
      active = false;
    };
  }, []);

  async function loadRecommendations() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getMentorRecommendations({ limit: 3 });
      setRecommendations(result);
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause
          : new ApiError("Could not load mentor recommendations.", 0),
      );
    } finally {
      setLoading(false);
    }
  }

  const greetingName = user?.name?.trim().split(/\s+/)[0];
  const profileName = supportingData.profile?.name?.trim().split(/\s+/)[0];
  const featuredMentor = recommendations?.items[0];
  const nextMentors = recommendations?.items.slice(1) ?? [];
  const graphNodeLabels = new Map(
    (supportingData.graph?.nodes ?? []).map((node) => [node.id, node.label]),
  );
  const meetingRequestIds = new Set(
    (supportingData.requests?.items ?? [])
      .filter((request) => request.status === "accepted")
      .map((request) => request.id),
  );

  async function sendMentorshipRequest() {
    if (!selectedMentor?.can_request || sendingRequest) return;
    const message = requestMessage.trim();
    if (message.length < 10 || message.length > 1500) {
      setRequestMessageError("Write an introduction between 10 and 1,500 characters.");
      return;
    }
    if (!window.confirm(`Send a mentorship request to ${selectedMentor.name}?`)) {
      return;
    }

    setSendingRequest(true);
    setRequestMessageError("");
    setRequestError("");
    setRequestSuccess("");
    try {
      await api.approveMentorRecommendation(selectedMentor.mentor_id);
      const created = await api.createMentorshipRequest({
        mentor_id: selectedMentor.mentor_id,
        message,
      });
      const deadline = created.deadline
        ? new Date(created.deadline).toLocaleString()
        : null;
      setRequestSuccess(
        `Request status: ${created.status}.${deadline ? ` Response deadline: ${deadline}.` : ""}`,
      );
      setRequestMessage("");
      await supportingData.loadRequests();
    } catch (cause) {
      setRequestError(
        cause instanceof ApiError
          ? cause.message
          : "The mentorship request could not be sent.",
      );
    } finally {
      setSendingRequest(false);
    }
  }

  function startProfileEdit() {
    const profile = supportingData.profile;
    if (!profile) return;
    setProfileHeadline(profile.headline ?? "");
    setProfileSkills(profile.skills.join(", "));
    setProfileBio(profile.bio ?? "");
    setProfileActionMessage("");
    setProfileActionError("");
    setEditingProfile(true);
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (savingProfile) return;
    setSavingProfile(true);
    setProfileActionMessage("");
    setProfileActionError("");
    try {
      await api.updateMyProfile({
        headline: profileHeadline.trim(),
        skills: profileSkills
          .split(/[,\n]/)
          .map((skill) => skill.trim())
          .filter(Boolean),
        bio: profileBio.trim(),
      });
      setProfileActionMessage("Your profile changes were saved.");
      setEditingProfile(false);
      await supportingData.loadProfile();
    } catch (cause) {
      setProfileActionError(
        cause instanceof ApiError
          ? cause.message
          : "Your profile could not be updated. Please try again.",
      );
    } finally {
      setSavingProfile(false);
    }
  }

  async function loadRequestDetails(requestId: string) {
    const sequence = ++requestDetailSequence.current;
    setViewingRequestId(requestId);
    setViewingRequest(null);
    setRequestDetailLoading(true);
    setRequestDetailError("");
    try {
      const detail = await api.getMentorshipRequest(requestId);
      if (sequence === requestDetailSequence.current) setViewingRequest(detail);
    } catch (cause) {
      if (sequence === requestDetailSequence.current) {
        setRequestDetailError(
          cause instanceof ApiError
            ? cause.message
            : "Request details could not be loaded.",
        );
      }
    } finally {
      if (sequence === requestDetailSequence.current) {
        setRequestDetailLoading(false);
      }
    }
  }

  return (
    <>
      <section className="dashboard-welcome">
        <div>
          <div className="eyebrow">YOUR CONNECTED COMMUNITY</div>
          <h1>{profileName || greetingName ? `Good to see you, ${profileName || greetingName}.` : "Welcome to connectED."}</h1>
          <p>Discover mentors, grow your network, and find your next opportunity.</p>
        </div>
        <Link className="button button-primary" to="/mentors">
          Find a mentor <ArrowUpRight size={16} />
        </Link>
      </section>

      {userError && (
        <div className="dashboard-profile-notice" role="status">
          {userError.status === 401 ? (
            <>
              Sign in to personalize your dashboard. <Link to="/login">Log in</Link>
            </>
          ) : (
            <>Your account profile could not be loaded: {userError.message}</>
          )}
        </div>
      )}
      {supportingData.profileError && (
        <div className="dashboard-profile-notice" role="status">
          Your profile details could not be loaded.{" "}
          {userError?.status === 401 ? <Link to="/login">Log in</Link> : supportingData.profileError}
          <button className="inline-retry" type="button" onClick={() => void supportingData.loadProfile()}>
            Retry
          </button>
        </div>
      )}
      {supportingData.profileLoading && (
        <div className="profile-summary-card" role="status">Loading your profile…</div>
      )}
      {supportingData.profile && (
        <section className="profile-summary-card" id="profile" aria-label="Your profile summary">
          <div className="profile-summary-icon"><GraduationCap size={19} /></div>
          <div className="profile-summary-copy">
            <strong>{supportingData.profile.headline || supportingData.profile.name}</strong>
            <span>
              {[supportingData.profile.degree, supportingData.profile.department, supportingData.profile.institution]
                .filter((value): value is string => Boolean(value?.trim()))
                .join(" · ") || "Profile details are ready to personalize your matches."}
            </span>
            {supportingData.profile.skills.length > 0 && (
              <div className="profile-summary-skills">
                {supportingData.profile.skills.slice(0, 5).map((skill) => (
                  <span className="skill-chip" key={skill}>{skill}</span>
                ))}
              </div>
            )}
          </div>
          <span className="profile-role-chip">{supportingData.profile.role}</span>
          <button
            className="button button-outline profile-edit-button"
            type="button"
            onClick={startProfileEdit}
          >
            <Pencil size={14} /> Edit profile
          </button>
        </section>
      )}
      {profileActionMessage && (
        <p className="dashboard-action-success" role="status">{profileActionMessage}</p>
      )}
      {profileActionError && (
        <p className="dashboard-action-error" role="alert">{profileActionError}</p>
      )}

      <section className="summary-grid" aria-label="Your networking overview">
        {summaryItems.map(({ label, detail, icon: Icon, metric }) => (
          <article className="summary-card" key={label}>
            <div className="summary-card-top">
              <span>{label}</span>
              <Icon size={17} />
            </div>
            <strong className={metric === "opportunities" ? "summary-unavailable" : undefined}>
              {metric === "recommendations"
                ? user?.role !== "student"
                  ? "—"
                  : loading ? "…" : recommendations?.total ?? "Unavailable"
                : metric === "pending"
                  ? supportingData.requestsLoading ? "…" : supportingData.pendingTotal ?? "Unavailable"
                  : metric === "accepted"
                    ? supportingData.requestsLoading ? "…" : supportingData.acceptedTotal ?? "Unavailable"
                    : supportingData.opportunitiesLoading
                      ? "…"
                      : supportingData.opportunities
                        ? supportingData.opportunities.length
                        : "Unavailable"}
            </strong>
            <small>
              {metric === "recommendations" && user?.role !== "student"
                ? "Available for student accounts"
                : metric === "opportunities" && supportingData.opportunities
                  ? "Listings loaded"
                : metric === "pending" && supportingData.pendingTotal === null &&
              !supportingData.requestsLoading
                ? "Could not load the server total"
                : metric === "accepted" && supportingData.acceptedTotal === null &&
                    !supportingData.requestsLoading
                  ? "Could not load the server total"
                  : detail}
            </small>
          </article>
        ))}
      </section>

      {user?.role === "student" && <section className="dashboard-feature-section">
        <div className="dashboard-section-heading">
          <div>
            <div className="eyebrow">A THOUGHTFUL PLACE TO START</div>
            <h2>Your next connection</h2>
            <p>Your top mentor recommendation, selected by the matching service.</p>
          </div>
          <Link className="text-link" to="/mentors">
            Explore all matches <ArrowRight size={15} />
          </Link>
        </div>

        {loading ? (
          <StatusView
            kind="loading"
            title="Finding your people"
            description="Loading recommendations from the connectED API…"
          />
        ) : error ? (
          <StatusView
            kind="error"
            title={error.status === 401 ? "Sign in to see your matches" : "Recommendations aren't available"}
            description={
              error.status === 401
                ? "This endpoint requires an account. Sign in to see your recommendations."
                : error.message
            }
            action={<RetryButton onClick={() => void loadRecommendations()} />}
          />
        ) : featuredMentor ? (
          <div className="featured-mentor-layout">
            <article className="featured-mentor-card">
              <div className="featured-card-orbit" aria-hidden="true">
                <span className="featured-orbit-ring" />
                <span className="featured-orbit-dot" />
                <Sparkles size={17} />
              </div>
              <div className="featured-mentor-copy">
                <div className="featured-overline">
                  <span className="live-dot" /> TOP RECOMMENDATION
                </div>
                <h3>{featuredMentor.name}</h3>
                <p className="featured-role">{featuredMentor.current_role}</p>
                {featuredMentor.profile_freshness && (
                  <span className="featured-freshness">
                    Profile {featuredMentor.profile_freshness}
                  </span>
                )}
                <div className="featured-tags">
                  {featuredMentor.skills.slice(0, 4).map((skill) => (
                    <span className="featured-tag" key={skill}>{skill}</span>
                  ))}
                </div>
                {featuredMentor.reasons.length > 0 && (
                  <div className="featured-reasons">
                    {featuredMentor.reasons.slice(0, 3).map((reason, index) => (
                      <span key={`${reason.code}-${index}`}>{reason.label}</span>
                    ))}
                  </div>
                )}
                <div className="featured-actions">
                  <button
                    className="button button-primary"
                    type="button"
                    onClick={() => setSelectedMentor(featuredMentor)}
                  >
                    View mentor <ArrowUpRight size={15} />
                  </button>
                  <Link className="featured-secondary-link" to="/mentors">
                    All matches <ArrowRight size={14} />
                  </Link>
                </div>
              </div>
              <div className="featured-score-wrap">
                <span className="featured-score">
                  {Number.isFinite(featuredMentor.match_score) &&
                  featuredMentor.match_score >= 0 &&
                  featuredMentor.match_score <= 1
                    ? <>
                        {Math.round(featuredMentor.match_score * 100)}
                        <small>%</small>
                      </>
                    : "—"}
                </span>
                <span className="featured-score-label">MATCH</span>
              </div>
            </article>
            <aside className="dashboard-aside-note">
              <div className="aside-note-icon"><Compass size={17} /></div>
              <h3>Good connections start with curiosity.</h3>
              <p>Explore the wider mentor community and find someone whose journey speaks to yours.</p>
              <Link to="/mentors">Discover mentors <ArrowRight size={14} /></Link>
            </aside>
          </div>
        ) : (
          <div className="dashboard-empty">
            <div className="empty-mark"><Sparkles size={21} /></div>
            <h3>No recommendations yet</h3>
            <p>There are no mentor matches available right now. Explore mentors to see what’s possible.</p>
            <Link className="button button-primary" to="/mentors">
              Explore mentors <ArrowRight size={15} />
            </Link>
          </div>
        )}
      </section>}

      <section className="dashboard-lower-grid" id="requests">
        <article className="dashboard-lower-card">
          <div className="dashboard-section-heading compact-heading">
            <div>
              <div className="eyebrow">KEEP THE MOMENTUM</div>
              <h2>My mentorship requests</h2>
            </div>
            {supportingData.requests && (
              <span className="results-count">{supportingData.requests.total} total</span>
            )}
          </div>
          {supportingData.requestsLoading ? (
            <StatusView kind="loading" title="Loading your requests" description="Fetching your latest mentorship activity." />
          ) : supportingData.requestsError ? (
            <StatusView
              kind="error"
              title="Requests aren't available"
              description={supportingData.requestsError}
              action={<RetryButton onClick={() => void supportingData.loadRequests()} />}
            />
          ) : supportingData.requests?.items.length ? (
            <div className="request-list">
              {supportingData.requests.items.map((request) => (
                <article className="request-row" key={request.id}>
                  <span className={`request-status request-status-${request.status}`}>
                    {request.status.replaceAll("_", " ")}
                  </span>
                  <div className="request-row-copy">
                    <strong>
                      {request.student_id === user?.id
                        ? `Mentor ID: ${request.mentor_id}`
                        : `Student ID: ${request.student_id}`}
                    </strong>
                    <span>Sent {formatDate(request.created_at) ?? "Date unavailable"}</span>
                    {request.status === "pending" && request.student_id === user?.id && (
                      <span>
                        Response deadline: {formatDate(request.deadline) ?? "Not provided"}
                      </span>
                    )}
                    <button
                      className="request-detail-link"
                      type="button"
                      onClick={() => void loadRequestDetails(request.id)}
                    >
                      View request details
                    </button>
                  </div>
                  {request.status === "pending" && (
                    <button
                      className="button button-outline request-cancel"
                      type="button"
                      disabled={supportingData.cancellingRequestId === request.id}
                      onClick={() => {
                        if (window.confirm("Cancel this mentorship request?")) {
                          void supportingData.cancelRequest(request.id);
                        }
                      }}
                    >
                      {supportingData.cancellingRequestId === request.id ? "Cancelling…" : "Cancel"}
                    </button>
                  )}
                  {request.status === "accepted" && (
                    <button
                      className="button button-outline request-cancel"
                      type="button"
                      onClick={() =>
                        setMeetingDraftRequestId((current) =>
                          current === request.id ? null : request.id,
                        )
                      }
                    >
                      {meetingDraftRequestId === request.id ? "Close" : "Propose time"}
                    </button>
                  )}
                  {meetingDraftRequestId === request.id && (
                    <form
                      className="meeting-proposal-form"
                      onSubmit={(event) => void submitMeetingProposal(event)}
                    >
                      <label htmlFor={`meeting-time-${request.id}`}>Proposed date and time</label>
                      <input
                        id={`meeting-time-${request.id}`}
                        type="datetime-local"
                        required
                        value={meetingDraftTime}
                        onChange={(event) => setMeetingDraftTime(event.target.value)}
                      />
                      <label htmlFor={`meeting-note-${request.id}`}>Note (optional)</label>
                      <textarea
                        id={`meeting-note-${request.id}`}
                        rows={2}
                        maxLength={500}
                        value={meetingDraftNote}
                        onChange={(event) => setMeetingDraftNote(event.target.value)}
                      />
                      <small>
                        Time zone: {Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC"}
                      </small>
                      <button
                        className="button button-primary request-cancel"
                        type="submit"
                        disabled={meetingActionBusy}
                      >
                        {meetingActionBusy ? "Sending…" : "Send proposal"}
                      </button>
                    </form>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <div className="unsupported-state">
              <div className="unsupported-icon"><MessageCircle size={17} /></div>
              <div>
                <strong>No mentorship requests yet</strong>
                <p>Send a request to a mentor and updates will appear here.</p>
              </div>
            </div>
          )}
          {(supportingData.requestActionMessage || supportingData.requestActionError) && (
            <p className={supportingData.requestActionError ? "dashboard-action-error" : "dashboard-action-success"} role="status">
              {supportingData.requestActionError || supportingData.requestActionMessage}
            </p>
          )}
        </article>
        <article className="dashboard-lower-card">
          <div className="dashboard-section-heading compact-heading">
            <div>
              <div className="eyebrow">STAY IN THE LOOP</div>
              <h2>Notifications</h2>
            </div>
          </div>
          {supportingData.notificationsLoading ? (
            <StatusView kind="loading" title="Loading notifications" description="Fetching your latest updates." />
          ) : supportingData.notificationsError ? (
            <StatusView
              kind="error"
              title="Notifications unavailable"
              description={supportingData.notificationsError}
              action={<RetryButton onClick={() => void supportingData.loadNotifications()} />}
            />
          ) : supportingData.notifications?.length ? (
            <div className="notification-list">
              {supportingData.notifications.map((notification) => (
                <article className={`notification-row${notification.read ? "" : " notification-unread"}`} key={notification.id}>
                  <span className="notification-dot" aria-hidden="true" />
                  <div>
                    <strong>{notification.title}</strong>
                    <p>{notification.message}</p>
                    <small>{formatDate(notification.created_at) ?? "Date unavailable"}</small>
                  </div>
                  <span className="notification-type">{notification.type.replaceAll("_", " ")}</span>
                </article>
              ))}
            </div>
          ) : (
            <div className="unsupported-state">
              <div className="unsupported-icon"><MessageCircle size={17} /></div>
              <div><strong>No notifications</strong><p>You’re up to date.</p></div>
            </div>
          )}
        </article>
      </section>

      <section className="dashboard-lower-card dashboard-meetings-card">
        <div className="dashboard-section-heading compact-heading">
          <div>
            <div className="eyebrow">MAKE TIME TO CONNECT</div>
            <h2>Meeting proposals</h2>
            <p>Propose a time for an accepted mentorship. A meeting is confirmed only after both participants accept.</p>
          </div>
        </div>
        {meetingActionMessage && <p className="dashboard-action-success" role="status">{meetingActionMessage}</p>}
        {meetingActionError && <p className="dashboard-action-error" role="alert">{meetingActionError}</p>}
        {supportingData.meetingsLoading ? (
          <StatusView kind="loading" title="Loading meeting proposals" description="Checking accepted mentorships." />
        ) : supportingData.meetingsError ? (
          <StatusView
            kind="error"
            title="Some proposals could not be loaded"
            description={supportingData.meetingsError}
            action={<RetryButton onClick={() => void supportingData.loadRequests()} />}
          />
        ) : supportingData.meetingProposals.length ? (
          <div className="meeting-list">
            {supportingData.meetingProposals.map((proposal) => {
              const canRespond =
                proposal.status === "proposed" ||
                proposal.status === "accepted_by_one";
              const alreadyAccepted = proposal.responses[user?.id ?? ""] === "accepted";
              return (
                <article className="meeting-row" key={proposal.id}>
                  <span className={`request-status request-status-${proposal.status}`}>
                    {proposal.status.replaceAll("_", " ")}
                  </span>
                  <div className="meeting-row-copy">
                    <strong>{formatDate(proposal.proposed_time) ?? "Proposed time unavailable"}</strong>
                    <span>{proposal.timezone_str}</span>
                    {proposal.note && <p>{proposal.note}</p>}
                    <small>Request {proposal.mentorship_request_id}</small>
                  </div>
                  {canRespond && !alreadyAccepted && (
                    <div className="meeting-actions">
                      <button
                        className="button button-outline request-cancel"
                        type="button"
                        disabled={meetingActionBusy}
                        onClick={() => void respondToMeeting(proposal.id, "decline")}
                      >
                        Decline
                      </button>
                      <button
                        className="button button-primary request-cancel"
                        type="button"
                        disabled={meetingActionBusy}
                        onClick={() => void respondToMeeting(proposal.id, "accept")}
                      >
                        Accept
                      </button>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="unsupported-state">
            <div className="unsupported-icon"><CalendarClock size={17} /></div>
            <div>
              <strong>No meeting proposals yet</strong>
              <p>{meetingRequestIds.size ? "Propose a time from an accepted mentorship request above." : "Meeting proposals are available after a mentorship request is accepted."}</p>
            </div>
          </div>
        )}
      </section>

      <section className="dashboard-insights-grid">
        <article className="dashboard-lower-card">
          <div className="dashboard-section-heading compact-heading">
            <div>
              <div className="eyebrow">GROW YOUR CIRCLE</div>
              <h2>Faculty &amp; research</h2>
              <p>Faculty recommendations returned by the matching service.</p>
            </div>
          </div>
          {supportingData.facultyLoading ? (
            <StatusView kind="loading" title="Finding faculty" description="Loading recommendations." />
          ) : supportingData.facultyError ? (
            <StatusView
              kind="error"
              title="Faculty recommendations unavailable"
              description={supportingData.facultyError}
              action={<RetryButton onClick={() => void supportingData.loadFaculty()} />}
            />
          ) : supportingData.faculty?.items.length ? (
            <div className="faculty-list">
              {supportingData.faculty.items.slice(0, 3).map((member) => (
                <article className="faculty-row" key={member.faculty_id}>
                  <span className="faculty-mark"><GraduationCap size={17} /></span>
                  <div>
                    <strong>{member.name}</strong>
                    <span>{[member.department, member.institution].filter(Boolean).join(" · ")}</span>
                    <small>{member.match_reason}</small>
                    <div className="faculty-areas">
                      {member.research_areas.slice(0, 3).map((area) => (
                        <span className="skill-chip" key={area}>{area}</span>
                      ))}
                    </div>
                  </div>
                  <span className="faculty-match">{Math.round(member.match_score * 100)}%</span>
                </article>
              ))}
            </div>
          ) : (
            <div className="unsupported-state">
              <div className="unsupported-icon"><GraduationCap size={17} /></div>
              <div><strong>No faculty recommendations</strong><p>The service returned no current matches.</p></div>
            </div>
          )}
          <div className="dashboard-subsection-heading">
            <strong>Research projects</strong>
            <span>Active opportunities from faculty</span>
          </div>
          {supportingData.researchLoading ? (
            <StatusView kind="loading" title="Loading research projects" description="Finding current projects." />
          ) : supportingData.researchError ? (
            <StatusView
              kind="error"
              title="Research projects unavailable"
              description={supportingData.researchError}
              action={<RetryButton onClick={() => void supportingData.loadResearchProjects()} />}
            />
          ) : supportingData.researchProjects?.length ? (
            <div className="research-list">
              {supportingData.researchProjects.slice(0, 3).map((project) => (
                <article className="research-row" key={project.id}>
                  <strong>{project.title}</strong>
                  <span>{project.faculty_name} · {project.research_area}</span>
                  <p>{project.description}</p>
                  <div className="faculty-areas">
                    {project.required_skills.slice(0, 4).map((skill) => (
                      <span className="skill-chip" key={skill}>{skill}</span>
                    ))}
                  </div>
                  <small>{project.availability.replaceAll("_", " ")}</small>
                  {project.application_instructions && (
                    <p className="research-instructions">{project.application_instructions}</p>
                  )}
                </article>
              ))}
            </div>
          ) : (
            <div className="unsupported-state">
              <div className="unsupported-icon"><GraduationCap size={17} /></div>
              <div><strong>No active research projects</strong><p>There are no projects available right now.</p></div>
            </div>
          )}
        </article>

        <article className="dashboard-lower-card">
          <div className="dashboard-section-heading compact-heading">
            <div>
              <div className="eyebrow">YOUR PROFESSIONAL NETWORK</div>
              <h2>Knowledge graph</h2>
            </div>
          </div>
          {supportingData.graphLoading ? (
            <StatusView kind="loading" title="Mapping your connections" description="Loading authorized graph data." />
          ) : supportingData.graphError ? (
            <StatusView
              kind="error"
              title="Knowledge graph unavailable"
              description={supportingData.graphError}
              action={<RetryButton onClick={() => void supportingData.loadGraph()} />}
            />
          ) : supportingData.graph?.nodes.length ? (
            <div className="graph-preview">
              <div className="graph-preview-summary">
                <span><strong>{supportingData.graph.nodes.length}</strong> nodes</span>
                <span><strong>{supportingData.graph.edges.length}</strong> connections</span>
              </div>
              <div className="graph-node-list">
                {supportingData.graph.nodes.slice(0, 8).map((node) => (
                  <span className="graph-node" key={node.id}>
                    {node.label}
                    <small>{node.type}</small>
                  </span>
                ))}
              </div>
              {supportingData.graph.edges.length > 0 && (
                <ul className="graph-connection-list" aria-label="Graph connections">
                  {supportingData.graph.edges.slice(0, 6).map((edge, index) => (
                    <li key={`${edge.source}-${edge.target}-${edge.type}-${index}`}>
                      <span>{graphNodeLabels.get(edge.source) ?? edge.source}</span>
                      <span className="graph-connection-type">{edge.type}</span>
                      <span>{graphNodeLabels.get(edge.target) ?? edge.target}</span>
                    </li>
                  ))}
                  {supportingData.graph.edges.length > 6 && (
                    <li className="graph-more-connections">
                      +{supportingData.graph.edges.length - 6} more connections
                    </li>
                  )}
                </ul>
              )}
            </div>
          ) : (
            <div className="unsupported-state">
              <div className="unsupported-icon"><Network size={17} /></div>
              <div><strong>Your graph is empty</strong><p>No nodes or connections were returned for your account.</p></div>
            </div>
          )}
        </article>
      </section>

      <section className="dashboard-lower-card dashboard-opportunities-card">
        <div className="dashboard-section-heading compact-heading">
          <div>
            <div className="eyebrow">WHAT'S NEXT</div>
            <h2>Opportunities</h2>
          </div>
        </div>
        {supportingData.opportunitiesLoading ? (
          <StatusView kind="loading" title="Loading opportunities" description="Fetching current listings." />
        ) : supportingData.opportunitiesError ? (
          <StatusView
            kind="error"
            title="Opportunities unavailable"
            description={supportingData.opportunitiesError}
            action={<RetryButton onClick={() => void supportingData.loadOpportunities()} />}
          />
        ) : supportingData.opportunities?.length ? (
          <div className="opportunity-grid">
            {supportingData.opportunities.map((opportunity) => {
              const applicationUrl = safeExternalUrl(opportunity.application_url);
              return (
                <article className="opportunity-card" key={opportunity.id}>
                  <div className="opportunity-card-top">
                    <span className="request-status">{opportunity.type}</span>
                    <span>{opportunity.location || "Location not specified"}</span>
                  </div>
                  <h3>{opportunity.title}</h3>
                  <strong>{opportunity.organization}</strong>
                  <p>{opportunity.description}</p>
                  {opportunity.required_skills.length > 0 && (
                    <div className="faculty-areas">
                      {opportunity.required_skills.slice(0, 5).map((skill) => (
                        <span className="skill-chip" key={skill}>{skill}</span>
                      ))}
                    </div>
                  )}
                  {opportunity.deadline && (
                    <small>Deadline: {formatDate(opportunity.deadline) ?? "Date unavailable"}</small>
                  )}
                  {applicationUrl ? (
                    <a href={applicationUrl} target="_blank" rel="noreferrer">
                      View application <ArrowUpRight size={14} />
                    </a>
                  ) : opportunity.contact_email ? (
                    <a href={`mailto:${opportunity.contact_email}`}>Contact the opportunity owner</a>
                  ) : null}
                </article>
              );
            })}
          </div>
        ) : (
          <div className="unsupported-state">
            <div className="unsupported-icon"><BriefcaseBusiness size={17} /></div>
            <div><strong>No opportunities listed</strong><p>Check back later for relevant opportunities.</p></div>
          </div>
        )}
      </section>

      <section className="dashboard-lower-card dashboard-communities-card">
        <div className="dashboard-section-heading compact-heading">
          <div>
            <div className="eyebrow">FIND YOUR PEOPLE</div>
            <h2>Communities</h2>
          </div>
        </div>
        {supportingData.communitiesLoading ? (
          <StatusView kind="loading" title="Loading communities" description="Finding groups to explore." />
        ) : supportingData.communitiesError ? (
          <StatusView
            kind="error"
            title="Communities unavailable"
            description={supportingData.communitiesError}
            action={<RetryButton onClick={() => void supportingData.loadCommunities()} />}
          />
        ) : supportingData.communities?.length ? (
          <div className="community-grid">
            {supportingData.communities.map((community) => (
              <article className="community-card" key={community.id}>
                <div className="community-card-top">
                  <span className="faculty-mark"><UsersRound size={17} /></span>
                  <span className="request-status">{community.category}</span>
                </div>
                <h3>{community.name}</h3>
                <p>{community.description}</p>
                <small>{community.member_count} members{community.is_private ? " · Private" : ""}</small>
              </article>
            ))}
          </div>
        ) : (
          <div className="unsupported-state">
            <div className="unsupported-icon"><UsersRound size={17} /></div>
            <div><strong>No communities available</strong><p>There are no discoverable communities right now.</p></div>
          </div>
        )}
      </section>

      {nextMentors.length > 0 && (
        <section className="dashboard-more-mentors">
          <div className="dashboard-section-heading">
            <div>
              <div className="eyebrow">MORE PEOPLE TO MEET</div>
              <h2>More recommendations</h2>
            </div>
            <Link className="text-link" to="/mentors">
              View all <ArrowRight size={15} />
            </Link>
          </div>
          <div className="mentor-grid">
            {nextMentors.map((mentor) => (
              <MentorCard
                key={mentor.mentor_id}
                mentor={mentor}
                onView={setSelectedMentor}
              />
            ))}
          </div>
        </section>
      )}

      {selectedMentor && (
        <div
          className="dialog-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setSelectedMentor(null);
          }}
        >
          <section
            className="mentor-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="dashboard-mentor-dialog-title"
          >
            <button
              className="dialog-close"
              type="button"
              aria-label="Close mentor details"
              onClick={() => setSelectedMentor(null)}
            >
              ×
            </button>
            <div className="avatar mentor-avatar dialog-avatar" aria-hidden="true">
              {selectedMentor.name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("")}
            </div>
            <div className="eyebrow section-eyebrow">MENTOR PROFILE</div>
            <h2 id="dashboard-mentor-dialog-title">{selectedMentor.name}</h2>
            <p className="dialog-role">{selectedMentor.current_role}</p>
            <div className="dialog-match">
              {Number.isFinite(selectedMentor.match_score) &&
              selectedMentor.match_score >= 0 &&
              selectedMentor.match_score <= 1
                ? `${Math.round(selectedMentor.match_score * 100)}% match`
                : "Match score unavailable"}
            </div>
            <h3>Why you're matched</h3>
            {selectedMentor.reasons.length > 0 ? (
              <ul className="dialog-reasons">
                {selectedMentor.reasons.map((reason, index) => (
                  <li key={`${reason.code}-${index}`}>{reason.label}</li>
                ))}
              </ul>
            ) : (
              <p className="muted-copy">No explanation was provided.</p>
            )}

            {editingProfile && (
              <div
                className="dialog-backdrop"
                role="presentation"
                onMouseDown={(event) => {
                  if (event.target === event.currentTarget) setEditingProfile(false);
                }}
              >
                <section
                  className="mentor-dialog profile-edit-dialog"
                  role="dialog"
                  aria-modal="true"
                  aria-labelledby="profile-edit-title"
                >
                  <button
                    className="dialog-close"
                    type="button"
                    aria-label="Close profile editor"
                    onClick={() => setEditingProfile(false)}
                  >
                    <X size={19} />
                  </button>
                  <div className="eyebrow section-eyebrow">YOUR PROFILE</div>
                  <h2 id="profile-edit-title">Edit profile details</h2>
                  <p className="muted-copy">Update the fields supported by your profile service.</p>
                  <form className="profile-edit-form" onSubmit={(event) => void saveProfile(event)}>
                    <label htmlFor="profile-headline">Headline</label>
                    <input
                      id="profile-headline"
                      value={profileHeadline}
                      onChange={(event) => setProfileHeadline(event.target.value)}
                      autoComplete="off"
                    />
                    <label htmlFor="profile-skills">Skills</label>
                    <textarea
                      id="profile-skills"
                      rows={3}
                      value={profileSkills}
                      onChange={(event) => setProfileSkills(event.target.value)}
                      aria-describedby="profile-skills-help"
                    />
                    <small id="profile-skills-help">Separate skills with commas or new lines.</small>
                    <label htmlFor="profile-bio">Bio</label>
                    <textarea
                      id="profile-bio"
                      rows={4}
                      value={profileBio}
                      onChange={(event) => setProfileBio(event.target.value)}
                    />
                    {profileActionError && (
                      <p className="dashboard-action-error" role="alert">{profileActionError}</p>
                    )}
                    <div className="profile-edit-actions">
                      <button
                        className="button button-outline"
                        type="button"
                        disabled={savingProfile}
                        onClick={() => setEditingProfile(false)}
                      >
                        Cancel
                      </button>
                      <button className="button button-primary" type="submit" disabled={savingProfile}>
                        {savingProfile ? "Saving…" : "Save changes"}
                      </button>
                    </div>
                  </form>
                </section>
              </div>
            )}

            {viewingRequestId && (
              <div
                className="dialog-backdrop"
                role="presentation"
                onMouseDown={(event) => {
                  if (event.target === event.currentTarget) {
                    requestDetailSequence.current += 1;
                    setViewingRequestId(null);
                  }
                }}
              >
                <section
                  className="mentor-dialog request-detail-dialog"
                  role="dialog"
                  aria-modal="true"
                  aria-labelledby="request-detail-title"
                >
                  <button
                    className="dialog-close"
                    type="button"
                    aria-label="Close request details"
                    onClick={() => {
                      requestDetailSequence.current += 1;
                      setViewingRequestId(null);
                    }}
                  >
                    <X size={19} />
                  </button>
                  <div className="eyebrow section-eyebrow">MENTORSHIP REQUEST</div>
                  <h2 id="request-detail-title">Request details</h2>
                  {requestDetailLoading ? (
                    <p role="status">Loading the request from the server…</p>
                  ) : requestDetailError ? (
                    <div>
                      <p className="dashboard-action-error" role="alert">{requestDetailError}</p>
                      <button
                        className="button button-outline"
                        type="button"
                        onClick={() => void loadRequestDetails(viewingRequestId)}
                      >
                        Retry
                      </button>
                    </div>
                  ) : viewingRequest ? (
                    <dl className="request-detail-list">
                      <div><dt>Status</dt><dd>{viewingRequest.status}</dd></div>
                      <div><dt>Mentor</dt><dd>{viewingRequest.mentor_id}</dd></div>
                      <div><dt>Request message</dt><dd>{viewingRequest.message}</dd></div>
                      <div><dt>Sent</dt><dd>{formatDate(viewingRequest.created_at) ?? "Date unavailable"}</dd></div>
                      {viewingRequest.response_at && (
                        <div><dt>Response</dt><dd>{formatDate(viewingRequest.response_at) ?? "Date unavailable"}</dd></div>
                      )}
                      {viewingRequest.deadline && (
                        <div><dt>Response deadline</dt><dd>{formatDate(viewingRequest.deadline) ?? "Date unavailable"}</dd></div>
                      )}
                      {viewingRequest.fallback_recommendation_id && (
                        <div><dt>Next recommendation</dt><dd>{viewingRequest.fallback_recommendation_id}</dd></div>
                      )}
                    </dl>
                  ) : null}
                </section>
              </div>
            )}
            <h3>Skills</h3>
            <div className="skill-list">
              {selectedMentor.skills.map((skill) => (
                <span className="skill-chip" key={skill}>{skill}</span>
              ))}
            </div>
            {selectedMentor.can_request ? (
              <div className="dashboard-request-form">
                <label htmlFor="dashboard-request-message">Your introduction</label>
                <textarea
                  id="dashboard-request-message"
                  rows={4}
                  value={requestMessage}
                  onChange={(event) => {
                    setRequestMessage(event.target.value);
                    setRequestMessageError("");
                    setRequestError("");
                    setRequestSuccess("");
                  }}
                  placeholder="Tell them what you hope to learn or discuss."
                  aria-invalid={Boolean(requestMessageError)}
                  aria-describedby={requestMessageError ? "dashboard-request-message-error" : undefined}
                />
                {requestMessageError && (
                  <span className="auth-field-error" id="dashboard-request-message-error">
                    {requestMessageError}
                  </span>
                )}
                <button
                  className="button button-primary"
                  type="button"
                  disabled={sendingRequest}
                  onClick={() => void sendMentorshipRequest()}
                >
                  {sendingRequest ? "Sending request…" : "Request mentorship"}
                  <ArrowUpRight size={15} />
                </button>
                {requestSuccess && <p className="dashboard-action-success" role="status">{requestSuccess}</p>}
                {requestError && <p className="dashboard-action-error" role="alert">{requestError}</p>}
              </div>
            ) : (
              <div className="dialog-notice">This mentor is not currently accepting requests.</div>
            )}
          </section>
        </div>
      )}
    </>
  );
}
