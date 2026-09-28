from database import SessionLocal

from rag.document_loader import load_meeting_documents
from rag.chunker import chunk_documents
from rag.embedding_service import create_embeddings
from rag.vector_store import (
    create_faiss_index,
    save_faiss_index,
    load_faiss_index
)


db = SessionLocal()

try:

    # 1. Load meetings
    documents = load_meeting_documents(db)

    # 2. Create chunks
    chunks = chunk_documents(
        documents,
        chunk_size=1200,
        chunk_overlap=100
    )

    # 3. Extract text
    texts = [
        chunk["content"]
        for chunk in chunks
    ]

    # 4. Generate embeddings
    embeddings = create_embeddings(texts)

    # 5. Create FAISS index
    index = create_faiss_index(
        embeddings
    )

    print("\nNumber of chunks:", len(chunks))

    print(
        "Number of vectors in FAISS:",
        index.ntotal
    )

    print(
        "Vector dimensions:",
        index.d
    )

    # 6. Save FAISS index
    save_faiss_index(index)

    print(
        "\nFAISS index saved successfully."
    )

    # 7. Test loading it again
    loaded_index = load_faiss_index()

    print(
        "FAISS index loaded successfully."
    )

    print(
        "Loaded vectors:",
        loaded_index.ntotal
    )

finally:

    db.close()