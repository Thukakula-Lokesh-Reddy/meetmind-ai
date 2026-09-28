MeetMind AI — Meeting Intelligence

Turn every meeting into action.

MeetMind AI is an AI-powered meeting intelligence system that transforms meeting recordings into structured, actionable information. It combines speech-to-text, speaker diarization, LLM-based analysis, PostgreSQL, and Retrieval-Augmented Generation (RAG) to help users understand meetings and interact with their meeting history through an AI assistant.

✨ Features
🎙️ Audio & Video Meeting Upload
📝 Automatic Speech-to-Text using WhisperX
👥 Speaker Diarization to distinguish speakers
🤖 AI Meeting Analysis using Gemini
📌 Automatic Extraction of
    Meeting summary
    Participants
    Decisions
    Action items
    Task owners
    Deadlines
📊 Meeting Dashboard for viewing and managing meetings
🔄 Processing Status Tracking
    Processing
    Analyzed
    Failed
🔁 Retry Failed Meeting Analysis
🗑️ Meeting & Action Item Management
🔎 RAG-based AI Assistant
💬 Ask Questions About Past Meetings
🎯 Meeting-specific AI Questions
📚 Source-aware AI Responses
🗄️ PostgreSQL Database
⚡ FastAPI REST API
⚛️ React Frontend

🏗️ System Architecture
                    ┌─────────────────────┐
                    │    React Frontend   │
                    │      Dashboard      │
                    └──────────┬──────────┘
                               │
                            REST API
                               │
                               ▼
                    ┌─────────────────────┐
                    │    FastAPI Backend  │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
       │ PostgreSQL  │  │  WhisperX   │  │   Gemini    │
       │  Database   │  │    STT +    │  │     LLM     │
       │             │  │ Diarization │  │   Analysis  │
       └─────────────┘  └─────────────┘  └─────────────┘
                                               │
                                               ▼
                                      ┌─────────────────┐
                                      │       RAG       │
                                      ├─────────────────┤
                                      │ Document Loader │
                                      │     Chunker     │
                                      │   Embeddings    │
                                      │      FAISS      │
                                      │    Retriever    │
                                      │   AI Assistant  │
                                      └─────────────────┘

🔄 Meeting Processing Pipeline
Meeting Audio / Video
        │
        ▼
     WhisperX
        │
        ├── Speech-to-Text
        │
        └── Speaker Diarization
        │
        ▼
     Transcript
        │
        ▼
      Gemini
        │
        ├── Summary
        ├── Participants
        ├── Decisions
        ├── Action Items
        ├── Owners
        └── Deadlines
        │
        ▼
    PostgreSQL
        │
        ▼
     React Dashboard

🧠 RAG Pipeline
MeetMind AI includes a Retrieval-Augmented Generation system that allows users to ask questions about their previous meetings.
PostgreSQL Meeting Data
        │
        ▼
 Document Loader
        │
        ▼
     Chunking
        │
        ▼
 Sentence Transformer
(all-MiniLM-L6-v2)
        │
        ▼
   384-D Embeddings
        │
        ▼
      FAISS
        │
        ▼
 Semantic + Keyword Retrieval
        │
        ▼
     Reranking
        │
        ▼
 Relevant Meeting Context
        │
        ▼
       Gemini
        │
        ▼
 AI Answer + Sources


RAG Components

| Component              | Responsibility                 
                              |
| ---------------------- | ------------------------------------------------------------ |
| `document_loader.py`   | Converts meeting information into searchable documents       |
| `chunker.py`           | Splits meeting documents into smaller retrievable chunks     |
| `embedding_service.py` | Generates embeddings using `all-MiniLM-L6-v2`                |
| `vector_store.py`      | Stores and searches embeddings using FAISS                   |
| `retriever.py`         | Retrieves and reranks relevant meeting chunks                |
| `rag_service.py`       | Orchestrates retrieval, context creation and Gemini response |

🛠️ Tech Stack
Frontend
React
Vite
Axios
CSS
Backend
Python
FastAPI
Pydantic
SQLAlchemy
AI / ML
WhisperX
Gemini
Sentence Transformers
all-MiniLM-L6-v2
FAISS
Database
PostgreSQL
Development
Git
GitHub
REST APIs
JSON

📂 Project Structure
meetmind-ai/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── llm_service.py
│       ├── whisper_service.py
│       │
│       └── rag/
│           ├── document_loader.py
│           ├── chunker.py
│           ├── embedding_service.py
│           ├── vector_store.py
│           ├── retriever.py
│           └── rag_service.py
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── App.css
│       ├── index.css
│       └── main.jsx
│
├── uploads/
├── .env.example
├── .gitignore
└── README.md


🎯 Project Goals

MeetMind AI was designed to address a common meeting-management problem: important decisions and action items can become difficult to track after a meeting.

The system aims to turn unstructured meeting conversations into structured information that users can:

    Review
    Search
    Track
    Question using natural language
    Use for follow-up actions
🔮 Future Improvements

Potential future improvements include:

    Background job processing for long meetings
    Faster Whisper models for lightweight deployments
    Improved RAG indexing and caching
    Better speaker-name resolution
    Email reminders for action items
    Advanced meeting analytics
    Authentication and role-based access control
    Production deployment with Docker
    Improved monitoring and error handling

👨‍💻 Author
Thukakula Lokesh Reddy

B.Tech — Computer Science

GitHub: Thukakula-Lokesh-Reddy

📄 License

This project is intended primarily as a learning and portfolio project