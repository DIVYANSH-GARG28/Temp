
import pandas as pd

INPUT_FILE = "data/alumni_cleaned.csv"
OUTPUT_FILE = "data/alumni_with_job_titles.csv"

# Each title is supported by a set of relevant skills.
ROLE_SKILLS = {
    "Machine Learning Engineer": {
        "machine learning": 3,
        "python": 1,
        "statistics": 1,
        "data science": 1,
        "deep learning": 2,
    },
    "AI Engineer": {
        "artificial intelligence": 3,
        "deep learning": 2,
        "machine learning": 2,
        "python": 1,
        "nlp": 2,
        "natural language processing": 2,
    },
    "Computer Vision Engineer": {
        "computer vision": 4,
        "deep learning": 2,
        "machine learning": 1,
        "python": 1,
    },
    "Data Scientist": {
        "data science": 3,
        "statistics": 2,
        "data analytics": 2,
        "data analysis": 2,
        "machine learning": 2,
        "python": 1,
    },
    "Data Analyst": {
        "data analytics": 3,
        "data analysis": 3,
        "statistics": 2,
        "sql": 2,
        "python": 1,
    },
    "Cybersecurity Engineer": {
        "cybersecurity": 4,
        "network security": 3,
    },
    "Cloud Engineer": {
        "cloud computing": 4,
        "aws": 3,
        "azure": 3,
    },
    "Frontend Developer": {
        "html": 2,
        "css": 2,
        "javascript": 2,
        "react": 3,
    },
    "Backend Developer": {
        "django": 3,
        "flask": 3,
        "node.js": 3,
        "express": 3,
        "sql": 1,
    },
    "Software Engineer": {
        "c++": 2,
        "java": 2,
        "python": 2,
        "javascript": 1,
        "data structures": 1,
    },
}


def infer_job_title(skills):
    skill_set = {
        skill.strip().lower()
        for skill in str(skills).split(",")
        if skill.strip()
    }

    scores = {
        role: sum(
            weight
            for skill, weight in role_skills.items()
            if skill in skill_set
        )
        for role, role_skills in ROLE_SKILLS.items()
    }

    best_role = max(scores, key=scores.get)
    best_score = scores[best_role]

    if best_score == 0:
        return "General Software / IT Professional"

    return best_role


df = pd.read_csv(INPUT_FILE)

df["job_title"] = df["skills"].apply(infer_job_title)
df["job_title_status"] = "inferred_from_skills"

df.to_csv(OUTPUT_FILE, index=False)

print("Rows processed:", len(df))
print("\nInferred job-title distribution:")
print(df["job_title"].value_counts())

print("\nSample results:")
print(
    df[["name", "skills", "job_title"]]
    .head(10)
    .to_string(index=False)
)

print("\nSaved to:", OUTPUT_FILE)
