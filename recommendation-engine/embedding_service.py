
from sentence_transformers import SentenceTransformer
from profile_processor import load_alumni_data, create_profile_text

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Load the model once and reuse it
_model = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def generate_embeddings(texts):
    """Convert profile text into normalized numerical embeddings."""
    if not texts:
        return []

    model = get_model()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    return embeddings


if __name__ == "__main__":
    df = load_alumni_data()
    df["profile_text"] = df.apply(create_profile_text, axis=1)

    embeddings = generate_embeddings(df["profile_text"].tolist())

    print("\nNumber of alumni:", len(df))
    print("Embedding matrix shape:", embeddings.shape)
    print("First alumni embedding (first 10 values):")
    print(embeddings[0][:10])
