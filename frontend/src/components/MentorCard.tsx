import { ArrowUpRight, Info, Sparkles } from "lucide-react";
import type { MentorRecommendation } from "../types/api";

interface MentorCardProps {
  mentor: MentorRecommendation;
  onView: (mentor: MentorRecommendation) => void;
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

function scorePercent(score: number): number | null {
  if (!Number.isFinite(score) || score < 0 || score > 1) return null;
  return Math.round(score * 100);
}

export function MentorCard({ mentor, onView }: MentorCardProps) {
  const match = scorePercent(mentor.match_score);

  return (
    <article className="mentor-card">
      <div className="mentor-card-top">
        <div className="avatar mentor-avatar" aria-hidden="true">{initials(mentor.name)}</div>
        <div className="match-pill">
          <Sparkles size={13} />
          {match === null ? "Score unavailable" : `${match}% match`}
        </div>
      </div>

      <div className="mentor-identity">
        <h2>{mentor.name}</h2>
        <p>{mentor.current_role}</p>
      </div>
      <div className="mentor-meta">
        <span className="verification-state">
          <Info size={13} />
          Verification status not included
        </span>
        {mentor.profile_freshness && (
          <span className={`freshness freshness-${mentor.profile_freshness}`}>
            Profile {mentor.profile_freshness}
          </span>
        )}
      </div>

      <div className="card-divider" />
      <div className="detail-label">WHY THIS MATCH</div>
      {mentor.reasons.length > 0 ? (
        <ul className="reason-list">
          {mentor.reasons.slice(0, 2).map((reason, index) => (
            <li key={`${reason.code}-${index}`}>
              <span className="reason-dot" />
              {reason.label}
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted-copy">No match explanation was provided.</p>
      )}

      <div className="skill-list" aria-label="Skills">
        {mentor.skills.slice(0, 4).map((skill) => (
          <span className="skill-chip" key={skill}>{skill}</span>
        ))}
        {mentor.skills.length > 4 && (
          <span className="skill-chip skill-chip-more">+{mentor.skills.length - 4}</span>
        )}
      </div>

      <button
        className="button button-secondary card-action"
        type="button"
        disabled={!mentor.can_request}
        onClick={() => onView(mentor)}
      >
        {mentor.can_request ? "View mentor" : "Not accepting requests"}
        {mentor.can_request && <ArrowUpRight size={16} />}
      </button>
    </article>
  );
}
