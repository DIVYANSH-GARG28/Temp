import { ArrowRight, Search, Sparkles } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { MentorCard } from "../components/MentorCard";
import { RetryButton, StatusView } from "../components/StatusView";
import { ApiError, api } from "../services/api";
import type {
  MentorRecommendation,
  MentorRecommendationsResponse,
} from "../types/api";

const PAGE_SIZE = 10;

export function MentorsPage() {
  const [searchParams] = useSearchParams();
  const [response, setResponse] = useState<MentorRecommendationsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [search, setSearch] = useState(() => searchParams.get("search") ?? "");
  const [selectedMentor, setSelectedMentor] =
    useState<MentorRecommendation | null>(null);
  const [offset, setOffset] = useState(0);

  const loadRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getMentorRecommendations({ limit: PAGE_SIZE, offset });
      setResponse(data);
    } catch (cause) {
      setError(
        cause instanceof ApiError
          ? cause
          : new ApiError("Something went wrong while loading mentors.", 0),
      );
    } finally {
      setLoading(false);
    }
  }, [offset]);

  useEffect(() => {
    void loadRecommendations();
  }, [loadRecommendations]);

  const mentors = useMemo(() => {
    const items = response?.items ?? [];
    const term = search.trim().toLowerCase();
    if (!term) return items;
    return items.filter((mentor) =>
      [mentor.name, mentor.current_role, ...mentor.skills]
        .join(" ")
        .toLowerCase()
        .includes(term),
    );
  }, [response, search]);

  return (
    <>
      <section className="hero-panel">
        <div className="hero-content">
          <div className="eyebrow"><Sparkles size={14} /> YOUR NEXT CHAPTER STARTS HERE</div>
          <h1>Good people.<br /><span>Better possibilities.</span></h1>
          <p>
            Meet alumni who have been where you want to go. Thoughtful matches,
            built around your goals.
          </p>
          <a className="hero-link" href="#recommendations">
            Explore your matches <ArrowRight size={16} />
          </a>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="orbit-core"><Sparkles size={26} /></div>
          <div className="orbit-node orbit-node-one">A</div>
          <div className="orbit-node orbit-node-two">M</div>
          <div className="orbit-node orbit-node-three">+</div>
        </div>
        <div className="hero-footnote">
          <span className="hero-footnote-dot" /> Recommendations from your community
        </div>
      </section>

      <section className="recommendations-section" id="recommendations">
        <div className="section-heading">
          <div>
            <div className="eyebrow section-eyebrow">MADE FOR YOUR JOURNEY</div>
            <h2>People worth knowing</h2>
            <p>Matches and explanations come directly from the recommendation service.</p>
          </div>
          {response && (
            <span className="results-count">
              {response.total} {response.total === 1 ? "match" : "matches"}
            </span>
          )}
        </div>

        <div className="filter-bar">
          <label className="search-field">
            <Search size={17} />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search these matches"
              aria-label="Search loaded mentor matches"
            />
            {search && (
              <button
                className="clear-search"
                type="button"
                aria-label="Clear search"
                onClick={() => setSearch("")}
              >
                ×
              </button>
            )}
          </label>
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
            title={error.status === 401 ? "Sign in to see your matches" : "We couldn't load your matches"}
            description={
              error.status === 401
                ? "Sign in to access your student recommendations."
                : error.message
            }
            action={<RetryButton onClick={() => void loadRecommendations()} />}
          />
        ) : mentors.length === 0 ? (
          <StatusView
            kind="empty"
            title={search ? "No matches for that search" : "Your next match is on its way"}
            description={
              search
                ? "Try a different name, role, or skill."
                : "There are no mentor recommendations to show right now. Complete your profile or check back soon."
            }
            action={search ? (
              <button className="button button-secondary" type="button" onClick={() => setSearch("")}>
                Clear search
              </button>
            ) : undefined}
          />
        ) : (
          <>
            <div className="mentor-grid">
              {mentors.map((mentor) => (
                <MentorCard
                  key={mentor.mentor_id}
                  mentor={mentor}
                  onView={setSelectedMentor}
                />
              ))}
            </div>
            {response && response.total > response.offset + response.limit && (
              <div className="pagination">
                <span>
                  Showing {response.offset + 1}–{response.offset + mentors.length} of {response.total}
                </span>
                <button
                  className="button button-secondary"
                  type="button"
                  onClick={() => setOffset((current) => current + PAGE_SIZE)}
                  disabled={loading}
                >
                  More matches <ArrowRight size={15} />
                </button>
              </div>
            )}
          </>
        )}
      </section>

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
            aria-labelledby="mentor-dialog-title"
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
            <h2 id="mentor-dialog-title">{selectedMentor.name}</h2>
            <p className="dialog-role">{selectedMentor.current_role}</p>
            <div className="dialog-match">{Math.round(selectedMentor.match_score * 100)}% match</div>
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
            <h3>Skills</h3>
            <div className="skill-list">
              {selectedMentor.skills.map((skill) => <span className="skill-chip" key={skill}>{skill}</span>)}
            </div>
            <div className="dialog-notice">
              Mentor profile details and the request form will be enabled when the backend confirms their response schemas.
            </div>
          </section>
        </div>
      )}
    </>
  );
}
