import json

from sqlalchemy.orm import Session

from models import Meeting


def load_meeting_documents(db: Session):
    """
    Load meeting information from PostgreSQL
    and convert each meeting into a structured
    text document suitable for RAG.
    """

    meetings = (
        db.query(Meeting)
        .order_by(Meeting.id)
        .all()
    )

    documents = []

    for meeting in meetings:

        # -----------------------------------------
        # Participants
        # -----------------------------------------

        participants_text = "\n".join(
            f"- {participant.name}"
            for participant in meeting.participants
        )

        if not participants_text:
            participants_text = "No participants recorded."

        # -----------------------------------------
        # Decisions
        # -----------------------------------------

        decisions_text = meeting.decisions

        if decisions_text:

            try:
                decisions = json.loads(decisions_text)

                if isinstance(decisions, list):

                    decisions_text = "\n".join(
                        f"- {decision}"
                        for decision in decisions
                    )

            except (json.JSONDecodeError, TypeError):

                pass

        else:

            decisions_text = "No decisions recorded."

        # -----------------------------------------
        # Action Items
        # -----------------------------------------

        action_items_text = meeting.action_items

        if action_items_text:

            try:
                action_items = json.loads(
                    action_items_text
                )

                if isinstance(action_items, list):

                    formatted_items = []

                    for item in action_items:

                        task = item.get(
                            "task",
                            "Unknown task"
                        )

                        owner = item.get(
                            "owner"
                        ) or "Unknown owner"

                        deadline = item.get(
                            "deadline"
                        ) or "No deadline"

                        formatted_items.append(
                            f"- Owner: {owner}\n"
                            f"  Task: {task}\n"
                            f"  Deadline: {deadline}"
                        )

                    action_items_text = "\n".join(
                        formatted_items
                    )

            except (json.JSONDecodeError, TypeError):

                pass

        else:

            action_items_text = (
                "No action items recorded."
            )

        # -----------------------------------------
        # Build RAG document
        # -----------------------------------------

        document = f"""
MEETING ID:
{meeting.id}

MEETING TITLE:
{meeting.title}

PARTICIPANTS:
{participants_text}

SUMMARY:
{meeting.summary or "No summary available."}

DECISIONS:
{decisions_text}

ACTION ITEMS:
{action_items_text}

TRANSCRIPT:
{meeting.transcript or "No transcript available."}
"""

        documents.append(
            {
                "meeting_id": meeting.id,
                "title": meeting.title,
                "content": document.strip(),
            }
        )

    return documents