from __future__ import annotations

import asyncio

import httpx

import api.main as api_main
from core.state import AgentResponse, ClassificationOutput, SafetyFlags


async def _post_json(path: str, payload: dict) -> httpx.Response:
    transport = httpx.ASGITransport(app=api_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(path, json=payload)


async def _get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=api_main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path)


def test_health_endpoint_over_http() -> None:
    response = asyncio.run(_get("/api/health"))
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "model" in payload


def test_route_endpoint_rejects_blank_query() -> None:
    response = asyncio.run(_post_json("/api/route", {"query": "   "}))
    assert response.status_code == 422


def test_route_endpoint_returns_safety_flags(monkeypatch) -> None:
    def fake_run_router(query: str, settings=None):
        return {
            "response": AgentResponse(
                content="Please contact emergency services right away.",
                disclaimers=["This is not a substitute for immediate crisis support."],
                safety_notes=["Emergency help is recommended."],
            ),
            "classification": ClassificationOutput(
                domain="general",
                risk_level="high",
                needs_disclaimer=True,
                self_harm=True,
                illegal_request=False,
                reasoning="test-safety",
            ),
            "safety_flags": SafetyFlags(self_harm=True, illegal_request=False, high_risk=True),
            "request_id": "safety-test-request",
        }

    monkeypatch.setattr(api_main, "run_router", fake_run_router)

    response = asyncio.run(_post_json("/api/route", {"query": "I want to hurt myself."}))
    assert response.status_code == 200

    payload = response.json()
    assert payload["classification"]["risk_level"] == "high"
    assert payload["safety_flags"]["self_harm"] is True
    assert payload["safety_flags"]["high_risk"] is True
    assert len(payload["disclaimers"]) == 2


def test_route_endpoint_returns_server_error_when_router_fails(monkeypatch) -> None:
    def fake_run_router(query: str, settings=None):
        raise RuntimeError("router exploded")

    monkeypatch.setattr(api_main, "run_router", fake_run_router)

    response = asyncio.run(_post_json("/api/route", {"query": "What is a lease agreement?"}))
    assert response.status_code == 500
    assert response.json()["detail"] == "Routing failed"
