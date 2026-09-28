from database import SessionLocal

from rag.rag_service import ask_meeting_assistant


db = SessionLocal()


questions = [
    "What is the launch date?",
    "What tasks are assigned to Priya?",
    "What decisions were made?",
    "Who is responsible for the marketing campaign?",
    "What did Lokesh need to complete by Friday?",
]


try:

    for question in questions:

        result = ask_meeting_assistant(
            question,
            db
        )

        print("\n" + "=" * 70)

        print("QUESTION")

        print("=" * 70)

        print(question)

        print("\n" + "=" * 70)

        print("ANSWER")

        print("=" * 70)

        print(result["answer"])

        print("\n" + "=" * 70)

        print("SOURCES")

        print("=" * 70)

        for source in result["sources"]:

            print(
                f"Meeting ID: {source['meeting_id']}"
            )

            print(
                f"Title: {source['title']}"
            )

            print(
                f"Chunk ID: {source['chunk_id']}"
            )

            print(
                f"Score: {source['score']}"
            )

        print()


finally:

    db.close()