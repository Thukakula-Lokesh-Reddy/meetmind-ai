import os

import faiss
import numpy as np


VECTOR_STORE_PATH = "rag/faiss_index"


def create_faiss_index(embeddings):
    """
    Create a FAISS index from embedding vectors.
    """

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index


def save_faiss_index(index):
    """
    Save the FAISS index to disk.
    """

    os.makedirs(
        VECTOR_STORE_PATH,
        exist_ok=True
    )

    faiss.write_index(
        index,
        f"{VECTOR_STORE_PATH}/meetings.index"
    )


def load_faiss_index():
    """
    Load the FAISS index from disk.
    """

    index_path = (
        f"{VECTOR_STORE_PATH}/meetings.index"
    )

    if not os.path.exists(index_path):
        raise FileNotFoundError(
            "FAISS index does not exist yet."
        )

    return faiss.read_index(index_path)