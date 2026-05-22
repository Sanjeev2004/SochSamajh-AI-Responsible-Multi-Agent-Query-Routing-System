"""
Async integration tests for the Medical & Legal Router API.
Tests use stronger, keyword-rich queries that reliably classify
via the heuristic pipeline without needing a live LLM API key.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app


@pytest.mark.asyncio
async def test_route_medical_query():
    """A clear symptom/medicine query must be classified as medical."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/route",
            json={"query": "I have fever, severe headache and vomiting since yesterday. Should I see a doctor?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["domain"] == "medical", (
            f"Expected 'medical', got '{data['classification']['domain']}'. "
            f"Reasoning: {data['classification'].get('reasoning')}"
        )


@pytest.mark.asyncio
async def test_route_legal_query():
    """A landlord/deposit/rights query must be classified as legal."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/route",
            json={"query": "My landlord is refusing to return my deposit after I moved out. What are my rights and can I file a complaint?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["domain"] == "legal", (
            f"Expected 'legal', got '{data['classification']['domain']}'. "
            f"Reasoning: {data['classification'].get('reasoning')}"
        )


@pytest.mark.asyncio
async def test_route_general_query():
    """A generic wellbeing query with no domain signals must be classified as general."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/route",
            json={"query": "How can I improve my general wellbeing and daily routine?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["domain"] == "general", (
            f"Expected 'general', got '{data['classification']['domain']}'. "
            f"Reasoning: {data['classification'].get('reasoning')}"
        )


@pytest.mark.asyncio
async def test_route_high_risk_medical():
    """A high-risk emergency query must be classified as medical + high risk."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/route",
            json={"query": "My father has chest pain and shortness of breath right now, what should I do?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["domain"] == "medical"
        assert data["classification"]["risk_level"] == "high"


@pytest.mark.asyncio
async def test_route_self_harm_intercepted():
    """A self-harm query must be intercepted by the pre-screen with safety flags."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/route",
            json={"query": "I want to kill myself, I can't cope anymore"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["safety_flags"]["self_harm"] is True
        assert data["classification"]["risk_level"] == "high"


@pytest.mark.asyncio
async def test_route_edge_case_legal_contract():
    """A contract/legal query must be classified as legal domain."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/route",
            json={"query": "How do I legally break a contract with my employer and what documents do I need?"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["domain"] == "legal"


@pytest.mark.asyncio
async def test_health_endpoint():
    """The health endpoint must return status ok."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
