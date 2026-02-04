from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from core.config import Settings, logger
from core.graph import run_router
from core.state import RouterResponse

settings = Settings.load()

app = FastAPI(title="Medical and Legal Query Router", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


class RouteRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)


@app.get("/api/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "model": settings.huggingface_model,
        "langsmith_project": settings.langsmith_project,
    }


@app.post("/api/route", response_model=RouterResponse)
async def route_query(payload: RouteRequest) -> RouterResponse:
    try:
        state = run_router(payload.query)
        response = state["response"]
        classification = state["classification"]
        safety_flags = state["safety_flags"]
        return RouterResponse(
            response=response.content,
            classification=classification,
            disclaimers=response.disclaimers + response.safety_notes,
            safety_flags=safety_flags,
            request_id=state.get("request_id", "unknown"),
        )
    except Exception as exc:  # pragma: no cover
        logger.exception("Routing failed")
        raise HTTPException(status_code=500, detail="Routing failed") from exc
