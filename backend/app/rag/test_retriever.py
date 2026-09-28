from database import SessionLocal

from rag.document_loader import load_meeting_documents
from rag.chunker import chunk_documents
from rag.retriever import retrieve_relevant_chunks


db = SessionLocal()


try:

    documents = load_meeting_documents(db)

    chunks = chunk_documents(
        documents,
        chunk_size=1200,
        chunk_overlap=100
    )

    questions = [
        "What decisions were made?",
        "What tasks are assigned to Priya?",
        "Who is responsible for the marketing campaign?",
    ]

    for question in questions:

        print("\n" + "=" * 80)
        print("QUESTION")
        print("=" * 80)
        print(question)

        results = retrieve_relevant_chunks(
            question,
            chunks,
            top_k=3
        )

        print("\n" + "=" * 80)
        print("RETRIEVED CHUNKS")
        print("=" * 80)

        for result in results:

            print(
                f"\nMeeting ID: {result['meeting_id']}"
            )

            print(
                f"Title: {result['title']}"
            )

            print(
                f"Chunk ID: {result['chunk_id']}"
            )

            print(
                f"Semantic Score: "
                f"{result['semantic_score']:.4f}"
            )

            print(
                f"Final Score: "
                f"{result['score']:.4f}"
            )

            print("\nCONTENT:")
            print(result["content"])

finally:

    db.close()