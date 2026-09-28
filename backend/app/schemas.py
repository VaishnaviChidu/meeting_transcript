from pydantic import BaseModel, Field


class Decision(BaseModel):
    description: str
    evidence: str = Field(description="Short exact or near-exact transcript support")


class ActionItem(BaseModel):
    description: str
    owner: str | None = None
    due_date: str | None = None
    evidence: str
    needs_clarification: bool = False


class MeetingExtraction(BaseModel):
    summary: str
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)


class ClarificationQuestion(BaseModel):
    id: str
    action_item_index: int
    field: str
    question: str
    evidence: str


class AnalyzeRequest(BaseModel):
    title: str = "Meeting notes"
    transcript: str = Field(min_length=20)


class ContextDocumentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=10)


class ClarificationRequest(BaseModel):
    answers: dict[str, str] = Field(description="Map clarification question IDs to answers")


class MeetingResponse(BaseModel):
    id: str
    title: str
    status: str
    summary: str = ""
    decisions: list[Decision] = Field(default_factory=list)
    action_items: list[ActionItem] = Field(default_factory=list)
    clarifications: list[ClarificationQuestion] = Field(default_factory=list)
