
import pandas as pd


def load_alumni_data(file_path="data/alumni_cleaned.csv"):
    """Load the cleaned alumni dataset."""
    df = pd.read_csv(file_path)

    required_columns = [
        "name", "department", "company",
        "batch", "skills", "email", "location"
    ]

    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing columns: {missing_columns}")

    return df


def create_profile_text(row):
    """Convert an alumni record into text for semantic matching."""
    return (
        f"Department: {row['department']}. "
        f"Company: {row['company']}. "
        f"Graduation batch: {row['batch']}. "
        f"Skills: {row['skills']}. "
        f"Location: {row['location']}."
    )


if __name__ == "__main__":
    df = load_alumni_data()
    df["profile_text"] = df.apply(create_profile_text, axis=1)

    print("Alumni profiles loaded:", len(df))
    print("\nExample profile:")
    print(df["profile_text"].iloc[0])
