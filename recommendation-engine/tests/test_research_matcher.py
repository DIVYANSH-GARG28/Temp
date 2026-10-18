
import pytest

from research_matcher import recommend_research_faculty


def test_returns_matching_faculty():
    results = recommend_research_faculty("Machine Learning")
    assert len(results) > 0


def test_synonym_matching():
    results = recommend_research_faculty("NLP")
    assert len(results) > 0
    assert all(
        "Natural Language Processing" in faculty["research_topics"]
        for faculty in results
    )


def test_unrelated_interest_returns_empty():
    results = recommend_research_faculty("Unrelated Topic XYZ")
    assert results == []


def test_empty_input_returns_empty():
    assert recommend_research_faculty("") == []
    assert recommend_research_faculty(["", "  "]) == []


def test_duplicate_interests_do_not_change_score():
    single = recommend_research_faculty("Machine Learning", top_n=1)
    duplicate = recommend_research_faculty(
        ["Machine Learning", "machine learning"],
        top_n=1,
    )

    assert single[0]["match_score"] == duplicate[0]["match_score"]


def test_top_n_limits_results():
    results = recommend_research_faculty("Machine Learning", top_n=3)
    assert len(results) <= 3


def test_results_are_ranked():
    results = recommend_research_faculty(
        "Machine Learning, Cybersecurity",
        top_n=10,
    )

    scores = [faculty["match_score"] for faculty in results]
    assert scores == sorted(scores, reverse=True)


def test_invalid_input_raises_error():
    with pytest.raises(TypeError):
        recommend_research_faculty(123)


def test_top_n_zero_or_negative_returns_empty():
    assert recommend_research_faculty("Machine Learning", top_n=0) == []
    assert recommend_research_faculty("Machine Learning", top_n=-5) == []


def test_tuple_input_is_supported():
    results = recommend_research_faculty(("Machine Learning", "NLP"), top_n=3)
    assert len(results) > 0


def test_string_with_extra_commas_and_whitespace():
    results = recommend_research_faculty("  Machine Learning , , NLP ,  ", top_n=3)
    assert len(results) > 0


def test_top_n_exceeding_pool_returns_all_matches():
    results = recommend_research_faculty("Machine Learning", top_n=100)
    assert 0 < len(results) <= 50


def test_invalid_element_in_interest_list_raises_type_error():
    with pytest.raises(TypeError):
        recommend_research_faculty(["Machine Learning", 456])


def test_invalid_top_n_types_raise_error():
    with pytest.raises(TypeError):
        recommend_research_faculty("Machine Learning", top_n=True)
    with pytest.raises(TypeError):
        recommend_research_faculty("Machine Learning", top_n="3")

