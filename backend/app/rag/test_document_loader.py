from database import SessionLocal
from rag.document_loader import load_meeting_documents


db = SessionLocal()

try:

    documents = load_meeting_documents(db)

    print("\nNumber of documents:", len(documents))

    for document in documents:

        print("\n" + "=" * 60)

        print("Meeting ID:", document["meeting_id"])

        print("Title:", document["title"])

        print("=" * 60)

        print(document["content"][:1500])

finally:

    db.close()