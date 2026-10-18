
"""
Research Faculty Matcher Prototype

Matches student research interests against faculty research areas using
keyword overlap and a hardcoded synonym map.

CRITICAL LIMITATIONS & SYNTHETIC DATA NOTICE:
- All 50 faculty profiles, universities, and research topics are COMPLETELY FICTIONAL.
- This is a prototype demonstration engine, NOT a production semantic ML matcher.
- Matching is keyword-overlap based with a synonym dictionary, not deep semantic embeddings.
- Match scores represent matched keyword proportions (0.0 to 1.0), not model confidence.
- Ties are broken deterministically by faculty name in alphabetical order.
"""

RESEARCH_AREAS = [
    ["Artificial Intelligence", "Machine Learning", "Deep Learning"],
    ["Natural Language Processing", "Machine Learning", "Information Retrieval"],
    ["Computer Vision", "Image Processing", "Deep Learning"],
    ["Data Science", "Statistics", "Data Mining"],
    ["Cybersecurity", "Network Security", "Cryptography"],
    ["Computer Networks", "Distributed Systems", "Cloud Computing"],
    ["Algorithms and Theory", "Optimization", "Graph Algorithms"],
    ["Software Engineering", "Software Testing", "DevOps"],
    ["Quantum Computing", "Quantum Algorithms", "Cryptography"],
    ["Internet of Things", "Embedded Systems", "Robotics"],
]

NAMES = [
    "Aarav Sharma", "Aditi Verma", "Arjun Mehta", "Ananya Rao",
    "Rohan Gupta", "Priya Nair", "Kabir Singh", "Ishita Das",
    "Vihaan Patel", "Meera Joshi", "Aditya Kumar", "Sana Khan",
    "Rahul Bose", "Neha Kapoor", "Karan Malhotra", "Tanya Roy",
    "Dev Shah", "Riya Sen", "Aryan Mishra", "Simran Kaur",
    "Nikhil Jain", "Kavya Reddy", "Manav Arora", "Diya Iyer",
    "Yash Thakur", "Pooja Menon", "Ishan Bhat", "Naina Sethi",
    "Reyansh Das", "Sara Ali", "Dhruv Khanna", "Avni Kulkarni",
    "Harsh Pandey", "Myra Thomas", "Siddharth Rao", "Kiara Gill",
    "Atharv Desai", "Zoya Sheikh", "Krish Bansal", "Anika Dutta",
    "Parth Trivedi", "Ira Chawla", "Samarth Roy", "Tara Pillai",
    "Neil Fernandes", "Lavanya Sinha", "Om Prakash", "Mira George",
    "Ritvik Anand", "Ayesha Mir"
]

UNIVERSITIES = [
    "Northstar University",
    "Cedar Valley Institute",
    "Riverview University",
    "Summit Technical University",
    "Lakeside Institute of Technology",
]

# Hardcoded synonyms for common research interests.
SYNONYMS = [
    {"ai", "artificial intelligence"},
    {"ml", "machine learning"},
    {"dl", "deep learning"},
    {"nlp", "natural language processing"},
    {"cv", "computer vision"},
    {"ir", "information retrieval"},
    {"iot", "internet of things"},
    {"ds", "data science"},
]


def topics_match(topic1, topic2):
    a = topic1.strip().casefold()
    b = topic2.strip().casefold()

    if a == b:
        return True

    # Match known abbreviations and synonyms.
    for group in SYNONYMS:
        if a in group and b in group:
            return True

    return False


# Create exactly 50 deterministic synthetic profiles.
FACULTY = [
    {
        "faculty_user_id": f"demo_{i + 1:03}",
        "faculty_name": name,
        "university": UNIVERSITIES[i % len(UNIVERSITIES)],
        "research_topics": RESEARCH_AREAS[i % len(RESEARCH_AREAS)].copy(),
        "homepage": "",
        "is_synthetic": True,
    }
    for i, name in enumerate(NAMES)
]




def recommend_research_faculty(research_interests, top_n=5):
    """
    Recommend synthetic faculty profiles based on keyword overlap with research interests.

    Parameters:
        research_interests (str | list[str] | tuple[str]): Comma-separated string or sequence
            of research interest topics.
        top_n (int): Maximum number of recommendations to return (default: 5).

    Returns:
        list[dict]: List of matching synthetic faculty dictionaries, ranked by descending
            match_score, with ties broken by faculty_name ascending.
    """
    if isinstance(research_interests, str):
        research_interests = [
            topic.strip()
            for topic in research_interests.split(",")
            if topic.strip()
        ]

    if not isinstance(research_interests, (list, tuple)):
        raise TypeError(
            "research_interests must be a string or list of strings"
        )

    if not all(isinstance(topic, str) for topic in research_interests):
        raise TypeError("Every research interest must be a string")

    if not isinstance(top_n, int) or isinstance(top_n, bool):
        raise TypeError("top_n must be an integer")

    if top_n <= 0 or not research_interests:
        return []

    # Remove empty and duplicate interests.
    original_interests = {}

    for topic in research_interests:
        topic = topic.strip()
        if topic:
            original_interests.setdefault(topic.casefold(), topic)

    interests = list(original_interests.keys())

    if not interests:
        return []

    recommendations = []

    for faculty in FACULTY:
        matched_topics = []

        for interest in interests:
            if any(
                topics_match(interest, faculty_topic)
                for faculty_topic in faculty["research_topics"]
            ):
                matched_topics.append(original_interests[interest])

        if not matched_topics:
            continue

        score = len(matched_topics) / len(interests)

        recommendations.append({
            **faculty,
            "match_score": round(score, 2),
            "match_reasons": [
                f"Research interest matched: {topic}"
                for topic in matched_topics
            ],
        })

    recommendations.sort(
        key=lambda item: (
            -item["match_score"],
            item["faculty_name"]
        )
    )

    return recommendations[:top_n]




if __name__ == "__main__":

    interests = input(
        "Enter research interests separated by commas: "
    )

    results = recommend_research_faculty(interests)

    if not results:
        print("No matching faculty found.")
    else:
        for faculty in results:
            print(f"\nFaculty: {faculty['faculty_name']}")
            print(f"University: {faculty['university']}")
            print(f"Research topics: {', '.join(faculty['research_topics'])}")
            print(f"Match score: {faculty['match_score']}")
            print(f"Reasons: {'; '.join(faculty['match_reasons'])}")
