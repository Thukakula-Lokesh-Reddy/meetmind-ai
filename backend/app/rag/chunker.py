def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
    """
    Split text into overlapping chunks.

    chunk_size:
        Maximum number of characters in each chunk.

    chunk_overlap:
        Number of characters repeated between
        consecutive chunks.
    """

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk.strip())

        start = end - chunk_overlap

    return chunks


def chunk_documents(
    documents: list[dict],
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
    """
    Convert meeting documents into smaller chunks
    while preserving meeting metadata.
    """

    chunked_documents = []

    for document in documents:

        chunks = chunk_text(
            document["content"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        for index, chunk in enumerate(chunks):

            chunked_documents.append(
                {
                    "meeting_id": document["meeting_id"],
                    "title": document["title"],
                    "chunk_id": index,
                    "content": chunk,
                }
            )

    return chunked_documents