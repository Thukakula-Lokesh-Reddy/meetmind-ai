from database import SessionLocal
from models import Meeting


db = SessionLocal()

try:

    meetings = (
        db.query(Meeting)
        .order_by(Meeting.id)
        .all()
    )

    print("\nTotal meetings:", len(meetings))

    for meeting in meetings:

        print("\n" + "=" * 70)

        print("Meeting ID:", meeting.id)
        print("Title:", meeting.title)

        print(
            "Transcript:",
            "YES" if meeting.transcript else "NO"
        )

        print(
            "Summary:",
            "YES" if meeting.summary else "NO"
        )

        print(
            "Decisions:",
            "YES" if meeting.decisions else "NO"
        )

        print(
            "Action Items:",
            "YES" if meeting.action_items else "NO"
        )

        print("=" * 70)

finally:

    db.close()