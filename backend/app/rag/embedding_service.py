from sentence_transformers import SentenceTransformer


# Load the embedding model once.
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(texts: list[str]):
    """
    Convert a list of text strings into numerical vectors.
    """

    if not texts:
        return []

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings