import re

from rag.embedding_service import create_embeddings
from rag.vector_store import load_faiss_index


STOP_WORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "what",
    "who",
    "when",
    "where",
    "which",
    "how",
    "did",
    "does",
    "do",
    "to",
    "of",
    "for",
    "in",
    "on",
    "and",
    "or",
    "with",
    "from",
    "about",
    "me",
    "tell",
    "please"
}


def _tokenize(text: str):

    words = re.findall(
        r"[a-zA-Z0-9]+",
        text.casefold()
    )

    return {
        word
        for word in words
        if word not in STOP_WORDS
        and len(word) > 2
    }


def _keyword_score(
    question: str,
    content: str
):

    question_words = _tokenize(
        question
    )

    content_words = _tokenize(
        content
    )


    if not question_words:

        return 0.0


    overlap = (
        question_words &
        content_words
    )


    score = (
        len(overlap) /
        len(question_words)
    )


    question_lower = question.casefold()
    content_lower = content.casefold()


    # ========================================================
    # SECTION BOOSTS
    # ========================================================

    if any(
        word in question_lower
        for word in [
            "decision",
            "decisions",
            "decided",
            "agreed"
        ]
    ):

        if "decisions:" in content_lower:

            score += 0.30


    if any(
        word in question_lower
        for word in [
            "task",
            "tasks",
            "action",
            "actions",
            "owner",
            "responsible",
            "assigned"
        ]
    ):

        if "action items:" in content_lower:

            score += 0.30


    if any(
        word in question_lower
        for word in [
            "participant",
            "participants",
            "attendee",
            "attendees"
        ]
    ):

        if "participants:" in content_lower:

            score += 0.30


    if any(
        word in question_lower
        for word in [
            "summary",
            "summarize",
            "overview"
        ]
    ):

        if "summary:" in content_lower:

            score += 0.30


    return score


def retrieve_relevant_chunks(
    question: str,
    chunks: list[dict],
    top_k: int = 6
):

    if not question.strip():

        return []


    if not chunks:

        return []


    # ========================================================
    # QUESTION EMBEDDING
    # ========================================================

    question_embedding = create_embeddings(
        [question]
    )


    # ========================================================
    # LOAD FAISS
    # ========================================================

    index = load_faiss_index()


    # ========================================================
    # RETRIEVE MORE CANDIDATES
    # ========================================================

    candidate_k = min(
        max(top_k * 4, 12),
        index.ntotal
    )


    scores, indices = index.search(
        question_embedding,
        candidate_k
    )


    candidates = []


    for semantic_score, index_position in zip(
        scores[0],
        indices[0]
    ):

        if index_position == -1:

            continue


        if index_position >= len(chunks):

            continue


        chunk = chunks[
            index_position
        ]


        keyword_score = _keyword_score(
            question,
            chunk["content"]
        )


        # Semantic similarity remains the strongest signal.
        #
        # Keyword/section relevance is a secondary signal.

        final_score = (
            float(semantic_score) * 0.70
            +
            keyword_score * 0.30
        )


        candidates.append(
            {
                "meeting_id": chunk[
                    "meeting_id"
                ],

                "title": chunk[
                    "title"
                ],

                "chunk_id": chunk[
                    "chunk_id"
                ],

                "content": chunk[
                    "content"
                ],

                "score": final_score
            }
        )


    # ========================================================
    # SORT BY FINAL RELEVANCE
    # ========================================================

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )


    # ========================================================
    # REMOVE DUPLICATE CHUNKS
    # ========================================================

    results = []

    seen = set()


    for candidate in candidates:

        key = (
            candidate["meeting_id"],
            candidate["chunk_id"]
        )


        if key in seen:

            continue


        seen.add(key)

        results.append(
            candidate
        )


        if len(results) >= top_k:

            break


    return results