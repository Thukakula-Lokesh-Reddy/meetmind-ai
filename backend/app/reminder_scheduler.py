
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

try:
    from .database import SessionLocal
    from .models import ActionItem, ReminderRecipient,ReminderLog
    from .email_service import send_action_item_reminder
except ImportError:
    from database import SessionLocal
    from models import ActionItem, ReminderRecipient,ReminderLog
    from email_service import send_action_item_reminder


IST = ZoneInfo("Asia/Kolkata")

scheduler = BackgroundScheduler(timezone=IST)


def get_reminder_candidates(db, today=None):
    """
    Find pending tasks due tomorrow or already overdue.
    Does not send emails or modify records.
    """
    if today is None:
        today = datetime.now(IST).date()

    tomorrow = today + timedelta(days=1)

    start_of_today = datetime.combine(
        today,
        time.min,
        tzinfo=IST
    )

    action_items = (
        db.query(ActionItem)
        .filter(
            ActionItem.status == "Pending",
            ActionItem.reminder_deadline.isnot(None),
            or_(
                ActionItem.reminder_deadline == tomorrow,
                ActionItem.reminder_deadline < today
            ),
            or_(
                ActionItem.last_reminded_at.is_(None),
                ActionItem.last_reminded_at < start_of_today
            )
        )
        .order_by(ActionItem.reminder_deadline.asc())
        .all()
    )

    candidates = []

    for item in action_items:
        if not item.owner or not item.owner.strip():
            continue

        recipient = (
            db.query(ReminderRecipient)
            .filter(
                func.lower(ReminderRecipient.name)
                == item.owner.strip().lower()
            )
            .first()
        )

        if not recipient or not recipient.email:
            continue

        email = recipient.email.strip()

        if email.lower().endswith("@example.com"):
            continue

        candidates.append({
            "id": item.id,
            "task": item.task,
            "owner": item.owner,
            "email": email,
            "deadline": item.reminder_deadline.isoformat(),
            "reason": (
                "Due tomorrow"
                if item.reminder_deadline == tomorrow
                else "Overdue"
            )
        })

    return candidates



def process_reminder_job(dry_run=True):
    """
    Preview reminders by default.

    Tracks attempts in ReminderLog and permits at most three
    attempts per action item, reminder type, and scheduled date.
    """
    db = SessionLocal()

    try:
        candidates = get_reminder_candidates(db)

        print(
            f"Automatic reminder job: "
            f"{len(candidates)} eligible task(s)."
        )

        if dry_run:
            for candidate in candidates:
                print("DRY RUN:", candidate)

            print("Dry run finished. No emails were sent.")
            return

        for candidate in candidates:
            item_id = candidate["id"]
            now = datetime.now(IST)
            today = now.date()

            reminder_type = (
                "due_tomorrow"
                if candidate["reason"] == "Due tomorrow"
                else "overdue"
            )

            log = None

            try:
                # Lock the task before checking its current state.
                item = (
                    db.query(ActionItem)
                    .filter(ActionItem.id == item_id)
                    .with_for_update()
                    .first()
                )

                if not item or item.status != "Pending":
                    continue

                if item.reminder_deadline is None:
                    continue

                if not (
                    item.reminder_deadline == today + timedelta(days=1)
                    or item.reminder_deadline < today
                ):
                    continue

                # Skip if this task was already reminded today.
                if item.last_reminded_at is not None:
                    last_sent = item.last_reminded_at

                    if last_sent.tzinfo is None:
                        last_sent = last_sent.replace(tzinfo=IST)

                    if last_sent >= datetime.combine(
                        today, time.min, tzinfo=IST
                    ):
                        continue

                # Always use the current recipient configuration.
                recipient = (
                    db.query(ReminderRecipient)
                    .filter(
                        func.lower(ReminderRecipient.name)
                        == item.owner.strip().lower()
                    )
                    .first()
                    if item.owner and item.owner.strip()
                    else None
                )

                if not recipient or not recipient.email:
                    continue

                email = recipient.email.strip()

                if email.lower().endswith("@example.com"):
                    continue

                # Find today's log for this reminder type.
                log = (
                    db.query(ReminderLog)
                    .filter(
                        ReminderLog.action_item_id == item_id,
                        ReminderLog.reminder_type == reminder_type,
                        ReminderLog.scheduled_for == today,
                    )
                    .with_for_update()
                    .first()
                )

                if log and log.status == "Sent":
                    print(
                        f"Skipping action item {item_id}: "
                        "this reminder was already sent today."
                    )
                    continue

                if log and log.attempt_count >= 3:
                    print(
                        f"Skipping action item {item_id}: "
                        "maximum three attempts reached."
                    )
                    continue

                # Create the daily log if it doesn't exist.
                if log is None:
                    log = ReminderLog(
                        action_item_id=item_id,
                        reminder_type=reminder_type,
                        scheduled_for=today,
                        status="Pending",
                        attempt_count=0,
                    )
                    db.add(log)

                    try:
                        db.flush()
                    except IntegrityError:
                        # Another worker may have created this log.
                        db.rollback()
                        print(
                            f"Skipping action item {item_id}: "
                            "a reminder log already exists."
                        )
                        continue

                # Persist the attempt BEFORE contacting SMTP.
                log.attempt_count += 1
                log.last_attempt_at = now
                log.status = "Pending"
                log.error_message = None
                db.commit()

                # Re-fetch after commit to work with current records.
                log = (
                    db.query(ReminderLog)
                    .filter(
                        ReminderLog.action_item_id == item_id,
                        ReminderLog.reminder_type == reminder_type,
                        ReminderLog.scheduled_for == today,
                    )
                    .with_for_update()
                    .first()
                )

                if not log or log.status == "Sent":
                    continue

                send_action_item_reminder(
                    recipient_email=email,
                    owner=item.owner,
                    task=item.task,
                    deadline=item.reminder_deadline.isoformat(),
                )

                # Mark the log and task only after sending succeeds.
                sent_time = datetime.now(IST)
                log.status = "Sent"
                log.sent_at = sent_time
                log.error_message = None
                item.last_reminded_at = sent_time
                db.commit()

                print(
                    f"Reminder sent for action item {item_id}. "
                    f"Attempt {log.attempt_count}/3."
                )

            except Exception as error:
                db.rollback()

                # Save the failure without losing the attempt count.
                try:
                    failed_log = (
                        db.query(ReminderLog)
                        .filter(
                            ReminderLog.action_item_id == item_id,
                            ReminderLog.reminder_type == reminder_type,
                            ReminderLog.scheduled_for == today,
                        )
                        .with_for_update()
                        .first()
                    )

                    if failed_log and failed_log.status != "Sent":
                        failed_log.status = "Failed"
                        failed_log.error_message = str(error)[:2000]
                        db.commit()

                except Exception as log_error:
                    db.rollback()
                    print(
                        f"Could not save failure log for task "
                        f"{item_id}: {log_error}"
                    )

                print(
                    f"Reminder failed for action item {item_id}: "
                    f"{error}"
                )

    finally:
        db.close()




def start_reminder_scheduler():
    """
    Run the automatic reminder job every day at 9:00 AM IST.
    """
    if not scheduler.running:
        scheduler.add_job(
            process_reminder_job,
            trigger="cron",
            hour=9,
            minute=0,
            id="meetmind_daily_reminders",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
            kwargs={"dry_run": False},
        )

        scheduler.start()

        print(
            "MeetMind AI automatic reminders scheduled "
            "daily at 9:00 AM IST."
        )


def stop_reminder_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("MeetMind AI reminder scheduler stopped.")
