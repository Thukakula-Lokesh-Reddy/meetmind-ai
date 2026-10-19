# MeetMind AI — Meeting Intelligence

**Turn every meeting into action.**

MeetMind AI transforms meeting audio and video into searchable, structured meeting intelligence. It combines speech recognition, speaker diarization, LLM-based analysis, PostgreSQL, and Retrieval-Augmented Generation (RAG).

## Features

- Audio and video meeting uploads
- Speech-to-text transcription using WhisperX
- Speaker diarization
- AI-generated meeting summaries
- Extraction of decisions, participants, action items, owners, and deadlines
- Meeting and action-item management
- Retry support for failed meeting analysis
- RAG-based AI assistant for questions about past meetings
- Meeting-specific retrieval and source-aware answers
- Manual email reminders for action items
- FastAPI REST API and React dashboard
- Docker Compose deployment with PostgreSQL

## Architecture

```text
React + Vite frontend
        |
        | HTTP / REST API
        v
FastAPI backend
        |
        +---- WhisperX: transcription and diarization
        |
        +---- Gemini: meeting analysis and AI answers
        |
        +---- Sentence Transformers + FAISS: RAG retrieval
        |
        +---- Email service: manual reminders
        |
        v
PostgreSQL database
```

### Meeting processing pipeline

1. Upload a supported audio or video recording.
2. WhisperX transcribes the recording and identifies speaker segments.
3. The LLM analyzes the transcript.
4. The application extracts the summary, decisions, participants, and action items.
5. Structured meeting information is stored in PostgreSQL.
6. The dashboard displays the results.

### RAG pipeline

1. Meeting content is converted into searchable documents.
2. Documents are split into retrievable chunks.
3. Sentence Transformers generates embeddings using `all-MiniLM-L6-v2`.
4. FAISS supports vector similarity search.
5. Retrieval and reranking select relevant meeting context.
6. Gemini generates an answer grounded in the retrieved context.

## Technology stack

| Area | Technologies |
|---|---|
| Frontend | React, Vite, Axios, CSS |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy |
| Speech processing | WhisperX |
| LLM | Google Gemini |
| RAG | Sentence Transformers, FAISS |
| Database | PostgreSQL |
| Email | SMTP |
| Containers | Docker, Docker Compose |

## Project structure

```text
meetmind-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── llm_service.py
│   │   ├── whisper_service.py
│   │   ├── email_service.py
│   │   ├── reminder_scheduler.py
│   │   └── rag/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   └── Dockerfile
├── uploads/                  # Local meeting files; not committed
├── compose.yaml
├── .env.example
├── .gitignore
├── .dockerignore
└── README.md
```

## Requirements

- Docker Desktop with Docker Compose
- A Gemini API key
- A Hugging Face token if required by the selected WhisperX diarization model
- SMTP credentials if email reminders are to be sent

The first build and first model initialization may take several minutes and download large dependencies or models.

## Run with Docker Compose

### 1. Clone the repository

```powershell
git clone https://github.com/Thukakula-Lokesh-Reddy/meetmind-ai.git
cd meetmind-ai
```

### 2. Configure environment variables

Create your local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Edit `.env` locally and set the required database credentials, Gemini API key, Hugging Face token, and any SMTP settings used by your configuration.

Never commit `.env` or paste its secrets into public issues or logs.

### 3. Build and start the services

```powershell
docker compose build
docker compose up -d
```

### 4. Check service status

```powershell
docker compose ps
docker compose logs --tail 100 backend
```

### 5. Open the application

- Frontend: http://localhost:8080
- FastAPI documentation: http://localhost:8000/docs

The frontend uses the API URL configured at build time. For remote deployments, configure `VITE_API_URL` to the appropriate reachable backend URL and rebuild the frontend.

### 6. Stop the application

```powershell
docker compose down
```

This stops and removes the containers but preserves the named PostgreSQL volume. Do not use `docker compose down -v` unless you intentionally want to remove that volume and its database data.

## Local development

For local development without Docker, install the Python dependencies from `backend/requirements.txt`, configure `.env`, start PostgreSQL, and run the backend from the directory expected by its imports.

Run the frontend from the `frontend` directory:

```powershell
npm install
npm run dev
```

Use the Docker workflow above for the simplest reproducible setup.

## Data and privacy

- Meeting recordings and transcripts can contain confidential information.
- Local uploads, database backups, environment files, and generated FAISS data should not be committed to Git.
- Docker stores PostgreSQL data in a named volume.
- The project currently provides manual email reminders; verify recipient configuration before sending messages.
- Back up important database data before making schema or deployment changes.

## Troubleshooting

View service logs:

```powershell
docker compose logs --tail 100 backend
docker compose logs --tail 50 frontend
docker compose logs --tail 50 db
```

Check running containers:

```powershell
docker compose ps
```

If the frontend cannot reach the API, verify that the backend is running, the configured API URL is correct, and the frontend origin is allowed by the backend CORS configuration.

If meeting analysis fails, inspect backend logs and verify the relevant API credentials and model access.

## Future improvements

- Background processing for long recordings
- Authentication and role-based access control
- Improved job status reporting and retry handling
- Enhanced monitoring and error reporting
- More advanced meeting analytics

## Author

**Thukakula Lokesh Reddy**

B.Tech, Computer Science

GitHub: [Thukakula-Lokesh-Reddy](https://github.com/Thukakula-Lokesh-Reddy)

## License

No license has been specified yet. Contact the author before reusing or redistributing this project.
