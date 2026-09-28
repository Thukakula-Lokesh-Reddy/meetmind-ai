from database import SessionLocal

from rag.document_loader import load_meeting_documents
from rag.chunker import chunk_documents
from rag.embedding_service import create_embeddings


db = SessionLocal()

try:

    # 1. Load meetings from PostgreSQL
    documents = load_meeting_documents(db)

    # 2. Split meetings into chunks
    chunks = chunk_documents(
        documents,
        chunk_size=1000,
        chunk_overlap=200
    )

    # 3. Extract text from every chunk
    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    # 4. Generate embeddings
    embeddings = create_embeddings(texts)

    print("\nNumber of chunks:", len(chunks))

    print("Number of embeddings:", len(embeddings))

    if len(embeddings) > 0:

        print(
            "Embedding dimensions:",
            embeddings.shape[1]
        )

        print(
            "\nFirst embedding:"
        )

        print(
            embeddings[0]
        )

finally:

    db.close()