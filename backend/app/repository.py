import json
import sqlite3
from pathlib import Path
from typing import Any


class MeetingRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS meetings (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    transcript TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    clarifications_json TEXT NOT NULL DEFAULT '[]'
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def save(
        self,
        meeting_id: str,
        title: str,
        transcript: str,
        status: str,
        result: dict[str, Any],
        clarifications: list[dict[str, Any]],
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT INTO meetings
                    (id, title, transcript, status, result_json, clarifications_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        status=excluded.status,
                        result_json=excluded.result_json,
                        clarifications_json=excluded.clarifications_json""",
                (
                    meeting_id,
                    title,
                    transcript,
                    status,
                    json.dumps(result),
                    json.dumps(clarifications),
                ),
            )

    def get(self, meeting_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "transcript": row["transcript"],
            "status": row["status"],
            "result": json.loads(row["result_json"]),
            "clarifications": json.loads(row["clarifications_json"]),
        }
