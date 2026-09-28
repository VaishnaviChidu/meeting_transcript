from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from backend.app.config import settings
from backend.app.context_store import ContextStore
from backend.app.repository import MeetingRepository
from backend.app.schemas import (
    AnalyzeRequest,
    ClarificationRequest,
    ContextDocumentRequest,
    MeetingResponse,
)
from backend.app.workflow import build_workflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    app.state.repository = MeetingRepository(settings.data_dir / "meetings.sqlite")
    app.state.context_store = None
    if settings.google_api_key:
        app.state.context_store = ContextStore(settings.data_dir / "vectors")
    with SqliteSaver.from_conn_string(str(settings.data_dir / "checkpoints.sqlite")) as checkpointer:
        checkpointer.setup()
        app.state.workflow = build_workflow(checkpointer)
        yield


app = FastAPI(title="Meetwise API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _meeting_payload(meeting_id: str, meeting: dict) -> dict:
    result = meeting["result"]
    return {
        "id": meeting_id,
        "title": meeting["title"],
        "status": meeting["status"],
        "summary": result.get("summary", ""),
        "decisions": result.get("decisions", []),
        "action_items": result.get("action_items", []),
        "clarifications": meeting.get("clarifications", []),
    }


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "google_api_configured": bool(settings.google_api_key)}


@app.post("/api/context")
def add_context(payload: ContextDocumentRequest, request: Request) -> dict[str, str]:
    store = request.app.state.context_store
    if store is None:
        raise HTTPException(status_code=503, detail="Configure GOOGLE_API_KEY before adding searchable context.")
    try:
        store.add(payload.title, payload.text)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not index context: {exc}") from exc
    return {"status": "indexed", "title": payload.title}


@app.post("/api/meetings", response_model=MeetingResponse)
def analyze_meeting(payload: AnalyzeRequest, request: Request) -> dict:
    if not settings.google_api_key:
        raise HTTPException(status_code=503, detail="Configure GOOGLE_API_KEY in .env to analyze a transcript.")

    meeting_id = str(uuid4())
    store = request.app.state.context_store
    try:
        context = store.search(payload.transcript) if store else []
        state = request.app.state.workflow.invoke(
            {"title": payload.title, "transcript": payload.transcript, "context": context},
            config={"configurable": {"thread_id": meeting_id}},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Meeting analysis failed: {exc}") from exc

    interruptions = state.get("__interrupt__", [])
    clarifications = interruptions[0].value.get("questions", []) if interruptions else []
    status = "needs_clarification" if interruptions else "complete"
    result = state.get("result", {})
    request.app.state.repository.save(
        meeting_id, payload.title, payload.transcript, status, result, clarifications
    )
    return _meeting_payload(
        meeting_id,
        {"title": payload.title, "status": status, "result": result, "clarifications": clarifications},
    )


@app.post("/api/meetings/{meeting_id}/clarifications", response_model=MeetingResponse)
def answer_clarifications(
    meeting_id: str, payload: ClarificationRequest, request: Request
) -> dict:
    repository = request.app.state.repository
    meeting = repository.get(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    if meeting["status"] != "needs_clarification":
        raise HTTPException(status_code=409, detail="This meeting has no pending clarifications.")
    expected = {item["id"] for item in meeting["clarifications"]}
    if not set(payload.answers).issubset(expected):
        raise HTTPException(status_code=400, detail="One or more clarification IDs are invalid.")
    try:
        state = request.app.state.workflow.invoke(
            Command(resume=payload.answers),
            config={"configurable": {"thread_id": meeting_id}},
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not apply clarification: {exc}") from exc
    result = state.get("result", meeting["result"])
    remaining = state.get("clarifications", [])
    status = "needs_clarification" if remaining else "complete"
    repository.save(
        meeting_id,
        meeting["title"],
        meeting["transcript"],
        status,
        result,
        remaining,
    )
    return _meeting_payload(
        meeting_id,
        {"title": meeting["title"], "status": status, "result": result, "clarifications": remaining},
    )


@app.get("/api/meetings/{meeting_id}", response_model=MeetingResponse)
def get_meeting(meeting_id: str, request: Request) -> dict:
    meeting = request.app.state.repository.get(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    return _meeting_payload(meeting_id, meeting)
