from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DB_PATH = DATA_DIR / "feedback.sqlite3"


def _ensure_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                request_id TEXT NOT NULL,
                query_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                rating TEXT NOT NULL CHECK (rating IN ('up', 'down'))
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_feedback_request_id ON feedback(request_id)"
        )
        connection.commit()


_ensure_db()


class FeedbackRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    response: str = Field(min_length=1, max_length=12000)
    rating: Literal["up", "down"]
    request_id: str = Field(min_length=1, max_length=128)


@router.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest) -> dict[str, str]:
    entry = (
        datetime.now(timezone.utc).isoformat(),
        feedback.request_id,
        feedback.query.strip(),
        feedback.response.strip(),
        feedback.rating,
    )

    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute(
                """
                INSERT INTO feedback (timestamp, request_id, query_text, response_text, rating)
                VALUES (?, ?, ?, ?, ?)
                """,
                entry,
            )
            connection.commit()
    except sqlite3.Error as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail="Failed to store feedback.") from exc

    return {"status": "success", "message": "Feedback received"}
