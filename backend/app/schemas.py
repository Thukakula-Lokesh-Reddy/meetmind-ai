from pydantic import BaseModel


class Participant(BaseModel):
    name: str


class ActionItem(BaseModel):
    task: str
    owner: str | None = None
    deadline: str | None = None


class MeetingAnalysis(BaseModel):
    participants: list[Participant]
    summary: str
    decisions: list[str]
    action_items: list[ActionItem]

class ChatRequest(BaseModel):
    question: str
    meeting_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]