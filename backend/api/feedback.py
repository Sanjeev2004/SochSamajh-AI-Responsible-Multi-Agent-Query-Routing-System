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


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


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


@router.get("/api/feedback/summary")
async def feedback_summary() -> dict:
    _ensure_db()
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        total = connection.execute("SELECT COUNT(*) AS count FROM feedback").fetchone()["count"]
        by_rating = connection.execute(
            """
            SELECT rating, COUNT(*) AS count
            FROM feedback
            GROUP BY rating
            ORDER BY rating
            """
        ).fetchall()
        recent_negative = connection.execute(
            """
            SELECT timestamp, request_id, query_text, response_text, rating
            FROM feedback
            WHERE rating = 'down'
            ORDER BY timestamp DESC
            LIMIT 10
            """
        ).fetchall()

    return {
        "total": total,
        "by_rating": [_row_to_dict(row) for row in by_rating],
        "negative_feedback_queue": [_row_to_dict(row) for row in recent_negative],
    }


@router.get("/api/feedback/failures")
async def feedback_failures(limit: int = 25) -> dict:
    _ensure_db()
    safe_limit = max(1, min(limit, 100))
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT timestamp, request_id, query_text, response_text
            FROM feedback
            WHERE rating = 'down'
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    return {
        "count": len(rows),
        "items": [_row_to_dict(row) for row in rows],
        "use": "Review these cases as candidates for new regression tests, dataset labels, or classifier/RAG tuning.",
    }
