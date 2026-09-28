from typing import Any, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from backend.app.config import settings
from backend.app.owners import extract_speaker_labels, validate_action_owners
from backend.app.schemas import MeetingExtraction


class MeetingState(TypedDict, total=False):
    title: str
    transcript: str
    context: list[str]
    result: dict[str, Any]
    clarifications: list[dict[str, Any]]
    answers: dict[str, str]


def _build_clarifications(result: dict[str, Any]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for index, item in enumerate(result.get("action_items", [])):
        evidence = item.get("evidence", "")
        if not item.get("owner"):
            questions.append(
                {
                    "id": f"action-{index}-owner",
                    "action_item_index": index,
                    "field": "owner",
                    "question": f"Who owns this action: {item.get('description', '')}?",
                    "evidence": evidence,
                }
            )
        if item.get("needs_clarification"):
            field = "due_date" if not item.get("due_date") else "description"
            subject = "the deadline" if field == "due_date" else "the action wording"
            questions.append(
                {
                    "id": f"action-{index}-{field}",
                    "action_item_index": index,
                    "field": field,
                    "question": f"Could you clarify {subject} for: {item.get('description', '')}?",
                    "evidence": evidence,
                }
            )
    return questions


def build_workflow(checkpointer: SqliteSaver):
    def extract(state: MeetingState) -> dict[str, Any]:
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is not configured. Copy .env.example to .env and add your key.")
        model = ChatGoogleGenerativeAI(
            model=settings.google_model,
            api_key=settings.google_api_key,
        ).with_structured_output(MeetingExtraction, method="json_schema")
        context = "\n\n".join(state.get("context", [])) or "No matching project context found."
        speakers = extract_speaker_labels(state["transcript"])
        speaker_list = ", ".join(speakers) if speakers else "No explicit speaker labels found."
        prompt = f"""Analyze this meeting transcript. Use only the transcript for claims about what was said.
Use project context only to resolve names or terminology; do not treat it as evidence of a decision.
Keep summary concise. Include decisions and action items only when supported by the transcript.
    Only assign an action owner when a speaker explicitly accepts or is clearly assigned the action, and that person matches one of the transcript speaker labels below. Otherwise leave owner null; never infer owners from context documents. Do not guess deadlines. Mark needs_clarification true when an action item is materially ambiguous.
For every decision and action item, provide brief transcript evidence.

Meeting title: {state.get('title', 'Meeting notes')}
    Transcript speaker labels: {speaker_list}
Project/team context (retrieved):
{context}

Transcript:
{state['transcript']}"""
        extraction = model.invoke(prompt)
        result = extraction.model_dump(mode="json")
        validate_action_owners(result, speakers)
        return {"result": result, "clarifications": _build_clarifications(result)}

    def request_clarification(state: MeetingState) -> dict[str, Any]:
        answers = interrupt({"questions": state.get("clarifications", [])})
        return {"answers": answers}

    def apply_answers(state: MeetingState) -> dict[str, Any]:
        result = dict(state["result"])
        items = [dict(item) for item in result.get("action_items", [])]
        answers = state.get("answers", {})
        for question in state.get("clarifications", []):
            answer = answers.get(question["id"], "").strip()
            if not answer:
                continue
            index = question["action_item_index"]
            if 0 <= index < len(items):
                items[index][question["field"]] = answer
                if question["field"] == "description":
                    items[index]["needs_clarification"] = False
        result["action_items"] = items
        return {"result": result, "clarifications": []}

    def route_after_extract(state: MeetingState) -> str:
        return "clarify" if state.get("clarifications") else "done"

    builder = StateGraph(MeetingState)
    builder.add_node("extract", extract)
    builder.add_node("clarify", request_clarification)
    builder.add_node("apply_answers", apply_answers)
    builder.add_edge(START, "extract")
    builder.add_conditional_edges("extract", route_after_extract, {"clarify": "clarify", "done": END})
    builder.add_edge("clarify", "apply_answers")
    builder.add_edge("apply_answers", END)
    return builder.compile(checkpointer=checkpointer)


__all__ = ["build_workflow", "Command"]
