import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app

@pytest.mark.asyncio
async def test_route_medical_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/route", json={"query": "What are the side effects of aspirin?"})
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["domain"] == "medical"

@pytest.mark.asyncio
async def test_route_legal_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/route", json={"query": "What are the requirements for filing a patent?"})
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["domain"] == "legal"

@pytest.mark.asyncio
async def test_route_general_query():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/route", json={"query": "How can I improve my general wellbeing and daily routine?"})
        assert response.status_code == 200
        data = response.json()
        # General wellbeing query
        assert data["classification"]["domain"] == "general"

@pytest.mark.asyncio
async def test_route_edge_case_query():
    """The classifier correctly identifies ambiguous queries like
    'How do I illegally break a contract?' as legal-domain (contract law),
    not as an illegal request. This validates the nuanced classification."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/route", json={"query": "How do I illegally break a contract?"})
        assert response.status_code == 200
        data = response.json()
        assert data["classification"]["domain"] == "legal"
