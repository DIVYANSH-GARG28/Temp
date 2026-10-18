
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


def test_matching_returns_empty_for_zero_or_negative_top_n():
    results_zero = recommend_mentors(
        student_skills="Python",
        target_career="Data Scientist",
        student_department="Computer Science",
        top_n=0
    )
    assert len(results_zero) == 0
    assert "match_score" in results_zero.columns

    results_neg = recommend_mentors(
        student_skills="Python",
        target_career="Data Scientist",
        student_department="Computer Science",
        top_n=-3
    )
    assert len(results_neg) == 0


def test_department_matching_case_and_whitespace_insensitive():
    results = recommend_mentors(
        student_skills="Python",
        target_career="Software Engineer",
        student_department="  computer science  ",
        top_n=5
    )
    # Alumni with Computer Science department should receive D=1.0
    for _, row in results.iterrows():
        if row["department"].strip().lower() == "computer science":
            assert row["D"] == 1.0


def test_empty_skills_handled_gracefully():
    results = recommend_mentors(
        student_skills="",
        target_career="Software Engineer",
        student_department="Computer Science",
        top_n=2
    )
    assert len(results) == 2
    assert results["matched_skills"].iloc[0] == ""


