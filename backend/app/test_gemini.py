import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Meeting
from schemas import MeetingAnalysis


load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# Connect to PostgreSQL
db: Session = SessionLocal()

meeting = (
    db.query(Meeting)
    .filter(Meeting.id == 6)
    .first()
)

if not meeting:
    print("Meeting 6 not found.")
    db.close()
    exit()

transcript = meeting.transcript

print("Full transcript length:", len(transcript))


# Use only the first 3000 characters
test_transcript = transcript[:3000]

print("Testing transcript length:", len(test_transcript))


prompt = f"""
You are an AI meeting assistant.

Analyze the meeting transcript below.

Return:

1. A concise summary.
2. Important decisions.
3. Action items.
4. Owner of each action item.
5. Deadline of each action item.

Rules:

- Do not invent information.
- Only use information present in the transcript.
- If an owner is unknown, use null.
- If a deadline is unknown, use null.
- Do not treat general discussion as an action item.

MEETING TRANSCRIPT:

{test_transcript}
"""


print("\nSending transcript to Gemini...")
print("Please wait...\n")


response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_schema": MeetingAnalysis,
    },
)


print("Gemini response received!\n")

print("RAW RESPONSE:")
print(response.text)


result = MeetingAnalysis.model_validate_json(response.text)

print("\nSUMMARY:")
print(result.summary)

print("\nDECISIONS:")
for decision in result.decisions:
    print("-", decision)

print("\nACTION ITEMS:")
for action in result.action_items:
    print("-", action)


db.close()