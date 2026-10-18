
from sklearn.metrics.pairwise import cosine_similarity

from profile_processor import load_alumni_data
from embedding_service import generate_embeddings, get_model


ALGORITHM_VERSION = "KCD-v1"
WEIGHTS = {"K": 0.50, "C": 0.30, "D": 0.20}


def recommend_mentors(
    student_skills,
    target_career,
    student_department,
    top_n=5
):
    df = load_alumni_data("data/alumni_with_job_titles.csv")
    model = get_model()

    # K: skill similarity
    student_embedding = model.encode(
        [f"Skills: {student_skills}"],
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    alumni_skill_texts = (
        "Skills: " + df["skills"].astype(str)
    ).tolist()

    alumni_skill_embeddings = generate_embeddings(alumni_skill_texts)

    K = cosine_similarity(
        student_embedding, alumni_skill_embeddings
    )[0]

    # C: career alignment using inferred job titles
    career_embedding = model.encode(
        [f"Career goal: {target_career}"],
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    job_title_embeddings = generate_embeddings(
        df["job_title"].astype(str).tolist()
    )

    C = cosine_similarity(
        career_embedding, job_title_embeddings
    )[0]

    # D: exact department match
    student_dept = str(student_department).strip().casefold()

    D = (
        df["department"].astype(str).str.strip().str.casefold()
        == student_dept
    ).astype(float).to_numpy()

    # Weighted score
    df["K"] = K
    df["C"] = C
    df["D"] = D

    df["match_score"] = (
        WEIGHTS["K"] * df["K"]
        + WEIGHTS["C"] * df["C"]
        + WEIGHTS["D"] * df["D"]
    )

    df["algorithm_version"] = ALGORITHM_VERSION

    # Explain recommendations using profile evidence
    student_skill_set = {
        skill.strip().lower()
        for skill in str(student_skills).split(",")
        if skill.strip()
    }

    def get_matched_skills(alumni_skills):
        alumni_skill_set = {
            skill.strip().lower()
            for skill in str(alumni_skills).split(",")
            if skill.strip()
        }

        return ", ".join(sorted(student_skill_set & alumni_skill_set))

    df["matched_skills"] = df["skills"].apply(get_matched_skills)

    def explain_match(row):
        evidence = []

        if row["matched_skills"]:
            evidence.append(f"Shared skills: {row['matched_skills']}")

        if row["C"] >= 0.60:
            evidence.append(
                f"Strong semantic similarity to target career "
                f"based on inferred job title (C={row['C']:.2f})"
            )
        else:
            evidence.append(
                f"Limited semantic similarity to target career "
                f"based on inferred job title (C={row['C']:.2f})"
            )

        if row["D"] == 1:
            evidence.append("Same academic department")

        return "; ".join(evidence)

    df["match_explanation"] = df.apply(explain_match, axis=1)

    # Rank mentors
    results = df.sort_values(
        ["match_score", "name"],
        ascending=[False, True],
        kind="stable"
    ).head(max(0, top_n))

    return results[
        [
            "name",
            "department",
            "company",
            "skills",
            "job_title",
            "K",
            "C",
            "D",
            "match_score",
            "matched_skills",
            "match_explanation",
            "algorithm_version"
        ]
    ]


if __name__ == "__main__":
    skills = input("Your skills (e.g. Python, statistics): ")
    career = input("Target career (e.g. ML Engineer): ")
    department = input("Your department (e.g. Computer Science): ")

    recommendations = recommend_mentors(
        student_skills=skills,
        target_career=career,
        student_department=department
    )

    print("\n--- Top Mentor Recommendations ---")

    if recommendations.empty:
        print("No mentor recommendations found.")
    else:
        print(recommendations.to_string(index=False))
