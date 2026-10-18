
import pytest

from matching_engine import recommend_mentors, WEIGHTS


def test_kcd_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_matching_returns_requested_number():
    results = recommend_mentors(
        student_skills="Python, machine learning",
        target_career="AI Engineer",
        student_department="Computer Science",
        top_n=3
    )

    assert len(results) == 3


def test_results_are_sorted_by_score():
    results = recommend_mentors(
        student_skills="Python, machine learning",
        target_career="AI Engineer",
        student_department="Computer Science",
        top_n=5
    )

    scores = results["match_score"].tolist()
    assert scores == sorted(scores, reverse=True)


def test_scores_follow_kcd_formula():
    results = recommend_mentors(
        student_skills="Python, machine learning",
        target_career="AI Engineer",
        student_department="Computer Science",
        top_n=3
    )

    expected = (
        WEIGHTS["K"] * results["K"]
        + WEIGHTS["C"] * results["C"]
        + WEIGHTS["D"] * results["D"]
    )

    assert (results["match_score"] - expected).abs().max() < 1e-9


def test_algorithm_version_is_present():
    results = recommend_mentors(
        student_skills="Python",
        target_career="Software Engineer",
        student_department="Computer Science",
        top_n=2
    )

    assert (results["algorithm_version"] == "KCD-v1").all()
    
def test_explanation_fields_are_present():
    results = recommend_mentors(
        student_skills="Python",
        target_career="AI Engineer",
        student_department="Computer Science",
        top_n=3
    )

    assert "matched_skills" in results.columns
    assert "match_explanation" in results.columns
    assert results["match_explanation"].notna().all()


def test_matched_skills_reflect_shared_skills():
    results = recommend_mentors(
        student_skills="Python",
        target_career="AI Engineer",
        student_department="Computer Science",
        top_n=5
    )

    for _, row in results.iterrows():
        alumni_skills = {
            skill.strip().lower()
            for skill in row["skills"].split(",")
        }

        if "python" in alumni_skills:
            assert "python" in row["matched_skills"].lower()

