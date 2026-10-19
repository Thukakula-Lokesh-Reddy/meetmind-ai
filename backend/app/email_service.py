import os
import smtplib

from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(
    os.getenv("SMTP_PORT", "587")
)
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")


def send_email(
    recipient_email: str,
    subject: str,
    body: str
):
    if not SMTP_HOST:
        raise RuntimeError(
            "SMTP_HOST is not configured."
        )

    if not SMTP_USERNAME:
        raise RuntimeError(
            "SMTP_USERNAME is not configured."
        )

    if not SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_PASSWORD is not configured."
        )

    if not SMTP_FROM_EMAIL:
        raise RuntimeError(
            "SMTP_FROM_EMAIL is not configured."
        )

    message = EmailMessage()

    message["From"] = SMTP_FROM_EMAIL
    message["To"] = recipient_email
    message["Subject"] = subject

    message.set_content(body)

    with smtplib.SMTP(
        SMTP_HOST,
        SMTP_PORT
    ) as server:

        server.starttls()

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        server.send_message(message)



def send_action_item_reminder(
    recipient_email: str,
    owner: str,
    task: str,
    deadline: str
):
    subject = "MeetMind AI | Action Item Reminder"

    body = f"""
Hello {owner},

This is an action item reminder from MeetMind AI.

Here are the details of your pending task:

Task: {task}
Deadline: {deadline}

Please complete the task by the specified deadline.

If you have already completed this task, you can disregard this reminder.

Best regards,
MeetMind AI
Meeting Intelligence
""".strip()

    send_email(
        recipient_email=recipient_email,
        subject=subject,
        body=body
    )
