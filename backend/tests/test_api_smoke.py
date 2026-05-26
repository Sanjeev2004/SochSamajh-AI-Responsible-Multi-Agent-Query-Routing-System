from __future__ import annotations

import asyncio

import api.main as api_main
from core.state import AgentResponse, ClassificationOutput, SafetyFlags


def test_health_route() -> None:
    payload = api_main.health_check()
    assert payload["status"] == "ok"


def test_route_endpoint_returns_router_response(monkeypatch) -> None:
    def fake_run_router(query: str, settings=None, **kwargs):
        return {
            "response": AgentResponse(
                content="Test response",
                disclaimers=["General educational information only."],
                safety_notes=[],
            ),
            "classification": ClassificationOutput(
                domain="medical",
                risk_level="medium",
                needs_disclaimer=True,
                self_harm=False,
                illegal_request=False,
                reasoning="test",
            ),
            "safety_flags": SafetyFlags(self_harm=False, illegal_request=False, high_risk=False),
            "request_id": "test-request-id",
        }

    monkeypatch.setattr(api_main, "run_router", fake_run_router)

    import httpx
    async def _post_json(path: str, payload: dict) -> httpx.Response:
        transport = httpx.ASGITransport(app=api_main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post(path, json=payload)

    payload = asyncio.run(_post_json("/api/route", {"query": "What is asthma?"})).json()

    assert payload["response"] == "Test response"
    assert payload["classification"]["domain"] == "medical"
    assert payload["request_id"] == "test-request-id"
