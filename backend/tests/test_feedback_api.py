from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path

import httpx

import api.main as api_main
import api.feedback as feedback_api


async def _post_json(path: str, payload: dict) -> httpx.Response:
    transport = httpx.ASGITransport(app=api_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=payload)


def test_feedback_endpoint_persists_record(monkeypatch, tmp_path: Path) -> None:
    temp_db = tmp_path / "feedback.sqlite3"
    monkeypatch.setattr(feedback_api, "DATA_DIR", tmp_path)
    monkeypatch.setattr(feedback_api, "DB_PATH", temp_db)
    feedback_api._ensure_db()

    response = asyncio.run(
        _post_json(
            "/api/feedback",
            {
                "request_id": "feedback-test-1",
                "query": "What can I do about a rent dispute?",
                "response": "Keep your lease and payment records.",
                "rating": "up",
            },
        )
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"

    with sqlite3.connect(temp_db) as connection:
        row = connection.execute(
            "SELECT request_id, query_text, response_text, rating FROM feedback"
        ).fetchone()

    assert row == (
        "feedback-test-1",
        "What can I do about a rent dispute?",
        "Keep your lease and payment records.",
        "up",
    )


def test_feedback_endpoint_rejects_invalid_rating(monkeypatch, tmp_path: Path) -> None:
    temp_db = tmp_path / "feedback.sqlite3"
    monkeypatch.setattr(feedback_api, "DATA_DIR", tmp_path)
    monkeypatch.setattr(feedback_api, "DB_PATH", temp_db)
    feedback_api._ensure_db()

    response = asyncio.run(
        _post_json(
            "/api/feedback",
            {
                "request_id": "feedback-test-2",
                "query": "Can you explain tenancy law?",
                "response": "Here is a short summary.",
                "rating": "maybe",
            },
        )
    )

    assert response.status_code == 422
