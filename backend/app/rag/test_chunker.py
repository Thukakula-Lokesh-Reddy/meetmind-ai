from database import SessionLocal

from rag.document_loader import load_meeting_documents
from rag.chunker import chunk_documents


db = SessionLocal()

try:

    documents = load_meeting_documents(db)

    chunks = chunk_documents(
        documents,
        chunk_size=1000,
        chunk_overlap=200
    )

    print("\nNumber of original documents:", len(documents))

    print("Number of chunks:", len(chunks))

    print("\nChunks by meeting:")

    meeting_chunk_counts = {}

    for chunk in chunks:

        meeting_id = chunk["meeting_id"]

        meeting_chunk_counts[meeting_id] = (
            meeting_chunk_counts.get(meeting_id, 0) + 1
        )

    for meeting_id, count in meeting_chunk_counts.items():

        title = next(
            document["title"]
            for document in documents
            if document["meeting_id"] == meeting_id
        )

        print(
            f"Meeting {meeting_id}: "
            f"{count} chunks - {title}"
        )

finally:

    db.close()