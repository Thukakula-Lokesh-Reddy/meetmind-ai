import os
from pathlib import Path
import json

from rag.rag_service import ask_meeting_assistant
from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from schemas import ChatRequest

from database import SessionLocal, engine, get_db
from models import Base, Meeting, Participant, ActionItem
from whisper_service import transcribe_audio
from llm_service import (
    AIServiceUnavailable,
    analyze_transcript
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="MeetMind AI API",
    description="AI-powered Meeting Intelligence API",
    version="1.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class MeetingCreate(BaseModel):
    title: str


class ActionItemStatusUpdate(BaseModel):
    status: str


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "MeetMind AI API is running"
    }


# ============================================================
# GET ALL MEETINGS
# ============================================================

@app.get("/meetings")
def get_meetings(
    db: Session = Depends(get_db)
):
    meetings = (
        db.query(Meeting)
        .order_by(Meeting.created_at.desc())
        .all()
    )

    return meetings


# ============================================================
# CREATE MEETING
# ============================================================

@app.post("/meetings")
def create_meeting(
    meeting: MeetingCreate,
    db: Session = Depends(get_db)
):
    new_meeting = Meeting(
        title=meeting.title,
        processing_status="Analyzed"
    )

    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    return new_meeting


# ============================================================
# GET SINGLE MEETING
# ============================================================

@app.get("/meetings/{meeting_id}")
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db)
):

    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id)
        .first()
    )

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    participants = (
        db.query(Participant)
        .filter(
            Participant.meeting_id == meeting.id
        )
        .order_by(Participant.id)
        .all()
    )

    action_items = (
        db.query(ActionItem)
        .filter(
            ActionItem.meeting_id == meeting.id
        )
        .order_by(ActionItem.id)
        .all()
    )

    decisions = []

    if meeting.decisions:

        try:
            decisions = json.loads(
                meeting.decisions
            )

        except json.JSONDecodeError:
            decisions = []

    return {
        "id": meeting.id,

        "title": meeting.title,

        "audio_filename": meeting.audio_filename,

        "processing_status": meeting.processing_status,

        "created_at": meeting.created_at,

        "participants": [
            {
                "id": participant.id,
                "name": participant.name
            }
            for participant in participants
        ],

        "summary": meeting.summary,

        "decisions": decisions,

        "action_items": [
            {
                "id": item.id,
                "task": item.task,
                "owner": item.owner,
                "deadline": item.deadline,
                "status": item.status
            }
            for item in action_items
        ],

        "transcript": meeting.transcript
    }


# ============================================================
# UPDATE MEETING
# ============================================================

@app.put("/meetings/{meeting_id}")
def update_meeting(
    meeting_id: int,
    meeting_data: MeetingCreate,
    db: Session = Depends(get_db)
):

    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id)
        .first()
    )

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    meeting.title = meeting_data.title

    db.commit()
    db.refresh(meeting)

    return meeting


# ============================================================
# DELETE MEETING
# ============================================================

@app.delete("/meetings/{meeting_id}")
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Find meeting
    # --------------------------------------------------------

    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id)
        .first()
    )

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    # --------------------------------------------------------
    # Remember uploaded filename before deleting DB record
    # --------------------------------------------------------

    audio_filename = meeting.audio_filename

    # --------------------------------------------------------
    # Delete meeting from database
    #
    # Because Participant and ActionItem relationships use
    # cascade="all, delete-orphan", their records are removed
    # together with the meeting.
    # --------------------------------------------------------

    db.delete(meeting)
    db.commit()

    # --------------------------------------------------------
    # Delete uploaded audio/video file
    # --------------------------------------------------------

    file_deleted = False

    if audio_filename:

        file_path = UPLOAD_DIR / Path(
            audio_filename
        ).name

        if file_path.exists():

            try:

                os.remove(file_path)

                file_deleted = True

            except OSError as error:

                print(
                    f"Warning: could not delete uploaded file "
                    f"{file_path}: {error}"
                )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "message": "Meeting deleted successfully",
        "meeting_id": meeting_id,
        "file_deleted": file_deleted
    }

# ============================================================
# MEETING PROCESSING HELPER
# ============================================================

def process_meeting_in_background(
    meeting_id: int,
    file_path: str | None = None
):
    """
    Process an uploaded meeting outside the upload request.

    Steps:
    1. Transcribe and diarize with WhisperX.
    2. Save the transcript.
    3. Analyze the transcript with Gemini.
    4. Save participants, decisions, summary and action items.
    5. Mark the meeting as Analyzed.

    If anything fails, the meeting is marked Failed.
    """

    db = SessionLocal()

    try:
        meeting = (
            db.query(Meeting)
            .filter(Meeting.id == meeting_id)
            .first()
        )

        if not meeting:
            print(
                f"Background processing stopped: "
                f"meeting {meeting_id} not found."
            )
            return

        meeting.processing_status = "Processing"
        db.commit()

        # --------------------------------------------------------
        # Transcribe + diarize OR reuse existing transcript
        # --------------------------------------------------------

        if file_path:

            print(
                f"Starting background transcription for "
                f"meeting {meeting_id}..."
            )

            transcript = transcribe_audio(file_path)

            meeting = (
                db.query(Meeting)
                .filter(Meeting.id == meeting_id)
                .first()
            )

            if not meeting:
                return

            meeting.transcript = transcript

            db.commit()

            print(
                f"Transcription completed for meeting "
                f"{meeting_id}."
            )

        else:

            transcript = meeting.transcript

            if not transcript:
                raise RuntimeError(
                    "Cannot retry analysis because "
                    "the meeting has no transcript."
                )

            print(
                f"Reusing existing transcript for "
                f"meeting {meeting_id}."
            )
        # --------------------------------------------------------
        # Gemini analysis
        # --------------------------------------------------------

        print(
            f"Starting Gemini analysis for "
            f"meeting {meeting_id}..."
        )

        analysis = analyze_transcript(transcript)

        # --------------------------------------------------------
        # Remove old analysis records
        # --------------------------------------------------------

        db.query(Participant).filter(
            Participant.meeting_id == meeting.id
        ).delete(
            synchronize_session=False
        )

        db.query(ActionItem).filter(
            ActionItem.meeting_id == meeting.id
        ).delete(
            synchronize_session=False
        )

        # --------------------------------------------------------
        # Save participants
        # --------------------------------------------------------

        saved_participants = []

        for participant in analysis.participants:

            name = participant.name.strip()

            if not name:
                continue

            new_participant = Participant(
                meeting_id=meeting.id,
                name=name
            )

            db.add(new_participant)
            saved_participants.append(new_participant)

        # --------------------------------------------------------
        # Save action items
        # --------------------------------------------------------

        saved_action_items = []

        for action in analysis.action_items:

            task = action.task.strip()

            if not task:
                continue

            new_action_item = ActionItem(
                meeting_id=meeting.id,
                task=task,
                owner=action.owner,
                deadline=action.deadline,
                status="Pending"
            )

            db.add(new_action_item)
            saved_action_items.append(new_action_item)

        # --------------------------------------------------------
        # Save decisions
        # --------------------------------------------------------

        meeting.decisions = json.dumps(
            analysis.decisions,
            ensure_ascii=False
        )

        # --------------------------------------------------------
        # Save summary
        # --------------------------------------------------------

        meeting.summary = analysis.summary

        # --------------------------------------------------------
        # Keep action_items JSON synchronized
        # --------------------------------------------------------

        meeting.action_items = json.dumps(
            [
                {
                    "task": action.task,
                    "owner": action.owner,
                    "deadline": action.deadline
                }
                for action in analysis.action_items
                if action.task.strip()
            ],
            ensure_ascii=False
        )

        # --------------------------------------------------------
        # Mark processing complete
        # --------------------------------------------------------

        meeting.processing_status = "Analyzed"

        db.commit()

        print(
            f"Meeting {meeting_id} processed successfully."
        )

    except Exception as error:

        db.rollback()

        print(
            f"Background processing failed for meeting "
            f"{meeting_id}: {repr(error)}"
        )

        try:
            failed_meeting = (
                db.query(Meeting)
                .filter(Meeting.id == meeting_id)
                .first()
            )

            if failed_meeting:
                failed_meeting.processing_status = "Failed"
                db.commit()

        except Exception as status_error:

            db.rollback()

            print(
                f"Could not update failed status for meeting "
                f"{meeting_id}: {repr(status_error)}"
            )

    finally:
        db.close()


# ============================================================
# UPLOAD MEETING
# ============================================================

@app.post("/meetings/upload")
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    filename = Path(
        file.filename
    ).name

    file_path = UPLOAD_DIR / filename

    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    try:

        with open(
            file_path,
            "wb"
        ) as file_object:

            file_object.write(
                await file.read()
            )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {str(error)}"
        )

    # --------------------------------------------------------
    # Create meeting immediately
    # --------------------------------------------------------

    new_meeting = Meeting(
        title=filename,
        audio_filename=filename,
        processing_status="Processing"
    )

    db.add(new_meeting)
    db.commit()
    db.refresh(new_meeting)

    # --------------------------------------------------------
    # Start background processing
    # --------------------------------------------------------

    background_tasks.add_task(
        process_meeting_in_background,
        new_meeting.id,
        str(file_path)
    )

    return {
        "message": "Meeting uploaded and processing started",
        "meeting_id": new_meeting.id,
        "filename": filename,
        "content_type": file.content_type,
        "processing_status": "Processing"
    }

# ============================================================
# RETRY FAILED MEETING ANALYSIS
# ============================================================

@app.post("/meetings/{meeting_id}/retry")
def retry_meeting_analysis(
    meeting_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Find meeting
    # --------------------------------------------------------

    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id)
        .first()
    )

    if not meeting:

        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    # --------------------------------------------------------
    # Only failed meetings can be retried
    # --------------------------------------------------------

    if meeting.processing_status != "Failed":

        raise HTTPException(
            status_code=400,
            detail=(
                "Only failed meetings can be retried."
            )
        )

    # --------------------------------------------------------
    # A transcript is required
    # --------------------------------------------------------

    if not meeting.transcript:

        raise HTTPException(
            status_code=400,
            detail=(
                "This meeting has no transcript. "
                "It must be uploaded again."
            )
        )

    # --------------------------------------------------------
    # Change status back to Processing
    # --------------------------------------------------------

    meeting.processing_status = "Processing"

    db.commit()

    # --------------------------------------------------------
    # Retry using the existing transcript
    # --------------------------------------------------------

    background_tasks.add_task(
        process_meeting_in_background,
        meeting.id
    )

    return {
        "message": (
            "Meeting analysis retry started."
        ),
        "meeting_id": meeting.id,
        "processing_status": "Processing"
    }

# ============================================================
# ANALYZE MEETING
# ============================================================

@app.post("/meetings/{meeting_id}/analyze")
def analyze_meeting(
    meeting_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Find meeting
    # --------------------------------------------------------

    meeting = (
        db.query(Meeting)
        .filter(Meeting.id == meeting_id)
        .first()
    )

    if not meeting:

        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    # --------------------------------------------------------
    # If background processing is still running
    # --------------------------------------------------------

    if meeting.processing_status == "Processing":

        return {
            "message": "Meeting is still being processed",
            "meeting_id": meeting.id,
            "processing_status": "Processing"
        }

    # --------------------------------------------------------
    # If background processing failed
    # --------------------------------------------------------

    if meeting.processing_status == "Failed":

        raise HTTPException(
            status_code=500,
            detail="Meeting processing failed. Please try uploading again."
        )

    # --------------------------------------------------------
    # Check transcript
    # --------------------------------------------------------

    if not meeting.transcript:

        raise HTTPException(
            status_code=400,
            detail="Meeting does not have a transcript"
        )

    # --------------------------------------------------------
    # Gemini analysis
    # --------------------------------------------------------

    try:

        analysis = analyze_transcript(
            meeting.transcript
        )

    except AIServiceUnavailable as error:

        raise HTTPException(
            status_code=503,
            detail=str(error)
        )

    except Exception as error:

        print(
            "Meeting analysis error:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Meeting analysis failed. "
                "Please try again."
            )
        )

    # --------------------------------------------------------
    # Remove old participants
    # --------------------------------------------------------

    db.query(Participant).filter(
        Participant.meeting_id == meeting.id
    ).delete(
        synchronize_session=False
    )

    # --------------------------------------------------------
    # Remove old action items
    # --------------------------------------------------------

    db.query(ActionItem).filter(
        ActionItem.meeting_id == meeting.id
    ).delete(
        synchronize_session=False
    )

    # --------------------------------------------------------
    # Save participants
    # --------------------------------------------------------

    saved_participants = []

    for participant in analysis.participants:

        name = participant.name.strip()

        if not name:
            continue

        new_participant = Participant(
            meeting_id=meeting.id,
            name=name
        )

        db.add(new_participant)

        saved_participants.append(
            new_participant
        )

    # --------------------------------------------------------
    # Save action items
    # --------------------------------------------------------

    saved_action_items = []

    for action in analysis.action_items:

        task = action.task.strip()

        if not task:
            continue

        new_action_item = ActionItem(
            meeting_id=meeting.id,
            task=task,
            owner=action.owner,
            deadline=action.deadline,
            status="Pending"
        )

        db.add(new_action_item)

        saved_action_items.append(
            new_action_item
        )

    # --------------------------------------------------------
    # Save decisions
    # --------------------------------------------------------

    meeting.decisions = json.dumps(
        analysis.decisions,
        ensure_ascii=False
    )

    # --------------------------------------------------------
    # Save summary
    # --------------------------------------------------------

    meeting.summary = analysis.summary

    # --------------------------------------------------------
    # Save action items JSON
    # --------------------------------------------------------

    meeting.action_items = json.dumps(
        [
            {
                "task": action.task,
                "owner": action.owner,
                "deadline": action.deadline
            }
            for action in analysis.action_items
            if action.task.strip()
        ],
        ensure_ascii=False
    )

    meeting.processing_status = "Analyzed"

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    db.commit()

    # --------------------------------------------------------
    # Refresh records
    # --------------------------------------------------------

    for participant in saved_participants:
        db.refresh(participant)

    for action_item in saved_action_items:
        db.refresh(action_item)

    db.refresh(meeting)

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "message": "Meeting analyzed successfully",

        "meeting_id": meeting.id,

        "processing_status": meeting.processing_status,

        "participants": [
            {
                "id": participant.id,
                "name": participant.name
            }
            for participant in saved_participants
        ],

        "summary": analysis.summary,

        "decisions": analysis.decisions,

        "action_items": [
            {
                "id": action_item.id,
                "task": action_item.task,
                "owner": action_item.owner,
                "deadline": action_item.deadline,
                "status": action_item.status
            }
            for action_item in saved_action_items
        ]
    }


# ============================================================
# GET ALL ACTION ITEMS
# ============================================================

@app.get("/action-items")
def get_action_items(
    db: Session = Depends(get_db)
):

    action_items = (
        db.query(ActionItem)
        .order_by(ActionItem.created_at.desc())
        .all()
    )

    return [
        {
            "id": item.id,
            "meeting_id": item.meeting_id,
            "task": item.task,
            "owner": item.owner,
            "deadline": item.deadline,
            "status": item.status,
            "created_at": item.created_at
        }
        for item in action_items
    ]


# ============================================================
# GET SINGLE ACTION ITEM
# ============================================================

@app.get("/action-items/{action_item_id}")
def get_action_item(
    action_item_id: int,
    db: Session = Depends(get_db)
):

    action_item = (
        db.query(ActionItem)
        .filter(
            ActionItem.id == action_item_id
        )
        .first()
    )

    if not action_item:

        raise HTTPException(
            status_code=404,
            detail="Action item not found"
        )

    return {
        "id": action_item.id,
        "meeting_id": action_item.meeting_id,
        "task": action_item.task,
        "owner": action_item.owner,
        "deadline": action_item.deadline,
        "status": action_item.status,
        "created_at": action_item.created_at
    }


# ============================================================
# UPDATE ACTION ITEM STATUS
# ============================================================

@app.put("/action-items/{action_item_id}/status")
def update_action_item_status(
    action_item_id: int,
    status_data: ActionItemStatusUpdate,
    db: Session = Depends(get_db)
):

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Completed"
    ]

    if status_data.status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. "
                "Use: Pending, In Progress, Completed"
            )
        )

    action_item = (
        db.query(ActionItem)
        .filter(
            ActionItem.id == action_item_id
        )
        .first()
    )

    if not action_item:

        raise HTTPException(
            status_code=404,
            detail="Action item not found"
        )

    action_item.status = status_data.status

    db.commit()

    db.refresh(action_item)

    return {
        "message": "Action item status updated successfully",

        "action_item": {
            "id": action_item.id,
            "meeting_id": action_item.meeting_id,
            "task": action_item.task,
            "owner": action_item.owner,
            "deadline": action_item.deadline,
            "status": action_item.status
        }
    }


# ============================================================
# DELETE ACTION ITEM
# ============================================================

@app.delete("/action-items/{action_item_id}")
def delete_action_item(
    action_item_id: int,
    db: Session = Depends(get_db)
):

    action_item = (
        db.query(ActionItem)
        .filter(
            ActionItem.id == action_item_id
        )
        .first()
    )

    if not action_item:

        raise HTTPException(
            status_code=404,
            detail="Action item not found"
        )

    db.delete(action_item)

    db.commit()

    return {
        "message": "Action item deleted successfully"
    }

# ============================================================
# AI CHAT
# ============================================================

@app.post("/chat")
def chat_with_meetings(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Ask questions about previous meetings
    using the RAG meeting assistant.
    """

    question = request.question.strip()


    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )


    # --------------------------------------------------------
    # Ask AI
    # --------------------------------------------------------

    try:

        result = ask_meeting_assistant(
            question,
            db,
            meeting_id=request.meeting_id
        )


        return result


    except AIServiceUnavailable as error:

        # Gemini may temporarily be unavailable.
        #
        # Return 503 instead of an unexplained 500.

        raise HTTPException(
            status_code=503,
            detail=str(error)
        )


    except Exception as error:

        print(
            "AI Assistant error:",
            repr(error)
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "The AI Assistant encountered an unexpected "
                "error. Please try again."
            )
        )