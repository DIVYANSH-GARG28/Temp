import math
import logging
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.exceptions import AppException
from app.repositories.profile_repository import profile_repo
from app.schemas.mentor import (
    MatchReason,
    MentorRecommendationItem,
    MentorRecommendationsResponse,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Embedding layer — explicit mode tracking
# EMBEDDING_MODE is set at import time and never silently switches.
# ---------------------------------------------------------------------------

class EmbeddingMode(str, Enum):
    MINILM = "minilm"   # Real all-MiniLM-L6-v2 (384-dim); semantically meaningful
    HASH = "hash"       # 64-dim token-frequency hash; NOT semantic — fallback only

_sentence_model = None
EMBEDDING_MODE: EmbeddingMode = EmbeddingMode.HASH  # conservative default

try:
    from sentence_transformers import SentenceTransformer
    _model_candidate = SentenceTransformer("all-MiniLM-L6-v2")
    # Verify the model actually produces 384-dimensional output
    _probe = _model_candidate.encode("probe").tolist()
    if len(_probe) != 384:
        raise RuntimeError(
            f"Unexpected embedding dimension {len(_probe)}; expected 384 for all-MiniLM-L6-v2."
        )
    _sentence_model = _model_candidate
    EMBEDDING_MODE = EmbeddingMode.MINILM
    logger.info(
        "Semantic matching active: all-MiniLM-L6-v2 loaded (384-dim). EMBEDDING_MODE=minilm"
    )
except ImportError:
    logger.warning(
        "sentence_transformers not installed. "
        "Semantic matching is DEGRADED — using 64-dim hash fallback. "
        "EMBEDDING_MODE=hash. "
        "Install: pip install sentence-transformers torch"
    )
except Exception as e:
    logger.error(
        "all-MiniLM-L6-v2 failed to load (%s). "
        "Semantic matching is DEGRADED — using 64-dim hash fallback. "
        "EMBEDDING_MODE=hash.",
        e,
    )


def _compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot_product / (norm_a * norm_b)))


def _embed_text_fallback(text: str) -> List[float]:
    """
    Deterministic 64-dim token-frequency hash.
    NOT semantically meaningful. Used only when all-MiniLM-L6-v2 is unavailable.
    """
    words = [w.lower() for w in text.split() if len(w) > 2]
    vec = [0.0] * 64
    for w in words:
        idx = hash(w) % 64
        vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


def encode_text(text: str) -> List[float]:
    """
    Encode text into a float vector.
    Returns 384-dim MiniLM embedding when the model is available,
    or 64-dim hash fallback otherwise.
    Check EMBEDDING_MODE to know which path is active.
    """
    if _sentence_model is not None:
        try:
            return _sentence_model.encode(text).tolist()
        except Exception as exc:
            logger.error("MiniLM encode failed for text snippet, falling back to hash: %s", exc)
    return _embed_text_fallback(text)


class MatchingService:
    async def get_mentor_recommendations(
        self,
        student_id: str,
        skill: Optional[str] = None,
        career_goal: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> MentorRecommendationsResponse:
        # 1. Retrieve student profile
        student_profile = await profile_repo.get_by_user_id(student_id)
        if not student_profile:
            raise AppException(
                code="STUDENT_PROFILE_REQUIRED",
                message="A student profile is required to generate mentor recommendations.",
                status_code=400,
            )

        student_skills = set(s.lower() for s in student_profile.get("skills", []))
        student_goals = student_profile.get("career_goals", [])
        if career_goal:
            student_goals = [career_goal] + student_goals

        student_text = (
            f"{student_profile.get('headline', '')} "
            f"{' '.join(student_goals)} "
            f"{' '.join(student_skills)} "
            f"{student_profile.get('bio', '')}"
        )
        student_vec = encode_text(student_text)

        # 2. Fetch candidate alumni from database
        candidate_alumni = await profile_repo.list_alumni(
            skill=skill, career_goal=career_goal, limit=100, offset=0
        )

        # 3. Calculate weighted scores and explainable reasons
        scored_candidates = []
        for alumni in candidate_alumni:
            if alumni.get("user_id") == str(student_id):
                continue

            alumni_skills = set(s.lower() for s in alumni.get("skills", []))
            alumni_text = (
                f"{alumni.get('headline', '')} "
                f"{alumni.get('current_role', '')} "
                f"{alumni.get('current_organization', '')} "
                f"{' '.join(alumni.get('skills', []))} "
                f"{alumni.get('bio', '')}"
            )
            alumni_vec = encode_text(alumni_text)

            # Cosine semantic similarity (35% weight)
            semantic_score = _compute_cosine_similarity(student_vec, alumni_vec)

            # Skill overlap (45% weight)
            matching_skills = student_skills.intersection(alumni_skills)
            skill_score = (
                len(matching_skills) / max(len(student_skills), 1)
                if student_skills
                else 0.5
            )
            skill_score = min(1.0, skill_score)

            # Freshness score (20% weight)
            freshness_raw = float(alumni.get("freshness_score", 0.9))
            freshness_score = min(1.0, max(0.1, freshness_raw))

            final_score = round(
                (0.45 * skill_score) + (0.35 * semantic_score) + (0.20 * freshness_score),
                2,
            )
            final_score = max(0.1, min(1.0, final_score))

            reasons: List[MatchReason] = []
            if matching_skills:
                reasons.append(
                    MatchReason(
                        code="SKILL_ALIGNMENT",
                        label=f"Aligned skills: {', '.join(list(matching_skills)[:3])}",
                    )
                )
            elif skill:
                reasons.append(
                    MatchReason(
                        code="SKILL_ALIGNMENT",
                        label=f"Strong expertise in requested skill: {skill}",
                    )
                )

            if semantic_score > 0.4:
                reasons.append(
                    MatchReason(
                        code="CAREER_ALIGNMENT",
                        label=f"Relevant experience in {alumni.get('current_role', 'Engineering')}",
                    )
                )

            if not reasons:
                reasons.append(
                    MatchReason(
                        code="NETWORK_MATCH",
                        label="Profile synergy and mentorship availability",
                    )
                )

            scored_candidates.append({
                "mentor_id": alumni["user_id"],
                "name": alumni.get("name", "Alumni Mentor"),
                "current_role": (
                    alumni.get("current_role") or alumni.get("headline") or "Alumni Mentor"
                ),
                "skills": alumni.get("skills", []),
                "match_score": final_score,
                "reasons": reasons,
                "profile_freshness": alumni.get("profile_freshness", "current"),
                "can_request": alumni.get("mentorship_preferences", {}).get(
                    "accepting_requests", True
                ),
            })

        # Sort descending by match_score (deterministic — no LLM in ranking path)
        scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)

        paginated_items = scored_candidates[offset: offset + limit]
        items = [MentorRecommendationItem(**item) for item in paginated_items]

        # Include embedding mode in algorithm_version so callers know which path is active
        alg_version = f"v1+{EMBEDDING_MODE.value}"

        return MentorRecommendationsResponse(
            items=items,
            algorithm_version=alg_version,
            total=len(scored_candidates),
            limit=limit,
            offset=offset,
        )


matching_service = MatchingService()

