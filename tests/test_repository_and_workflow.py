from backend.app.repository import MeetingRepository
from backend.app.owners import extract_speaker_labels, validate_action_owners
from backend.app.workflow import _build_clarifications
from fastapi.testclient import TestClient


def test_clarification_questions_for_missing_owner_and_uncertain_action() -> None:
    result = {
        "action_items": [
            {
                "description": "Follow up with the customer team",
                "owner": None,
                "due_date": None,
                "evidence": "Someone should follow up with the customer team.",
                "needs_clarification": True,
            }
        ]
    }

    questions = _build_clarifications(result)

    assert [question["field"] for question in questions] == ["owner", "due_date"]
    assert all(question["evidence"] == result["action_items"][0]["evidence"] for question in questions)


def test_owner_must_match_an_explicit_transcript_speaker() -> None:
    transcript = "[00:02] Maya: We need the launch checklist.\nJordan: I can own it.\n"
    speakers = extract_speaker_labels(transcript)
    result = {
        "action_items": [
            {"description": "Prepare the checklist", "owner": "Jordan", "needs_clarification": False},
            {"description": "Contact the vendor", "owner": "Alex", "needs_clarification": False},
        ]
    }

    validate_action_owners(result, speakers)

    assert speakers == ["Maya", "Jordan"]
    assert result["action_items"][0]["owner"] == "Jordan"
    assert result["action_items"][1]["owner"] is None
    assert result["action_items"][1]["needs_clarification"] is True


def test_meeting_repository_round_trip(tmp_path) -> None:
    repository = MeetingRepository(tmp_path / "meetings.sqlite")
    result = {"summary": "A concise recap", "decisions": [], "action_items": []}

    repository.save("meeting-1", "Planning", "Transcript content", "complete", result, [])
    meeting = repository.get("meeting-1")

    assert meeting is not None
    assert meeting["title"] == "Planning"
    assert meeting["transcript"] == "Transcript content"
    assert meeting["result"] == result
    assert meeting["status"] == "complete"


def test_api_starts_without_key_and_explains_setup(monkeypatch, tmp_path) -> None:
    from backend.app.config import settings
    from backend.app.main import app

    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "google_api_key", None)

    with TestClient(app) as client:
        health = client.get("/api/health")
        response = client.post(
            "/api/meetings",
            json={"title": "Planning", "transcript": "A sufficiently long sample transcript."},
        )

    assert health.status_code == 200
    assert health.json()["google_api_configured"] is False
    assert response.status_code == 503
    assert "GOOGLE_API_KEY" in response.json()["detail"]
