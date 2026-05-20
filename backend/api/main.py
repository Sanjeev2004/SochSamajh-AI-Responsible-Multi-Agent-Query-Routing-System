from __future__ import annotations

from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional

from core.config import Settings, logger
from core.graph import run_router
from core.state import RouterResponse
from api.feedback import router as feedback_router

settings = Settings.load()

app = FastAPI(title="Medical and Legal Query Router", version="1.0.0")

@app.on_event("startup")
async def warmup_retriever():
    from agents.retriever import retriever
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, retriever._initialize)
    logger.info("Retriever warmed up on startup")

app.include_router(feedback_router)

allow_credentials = True
if "*" in settings.backend_cors_origins:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error for {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later.", "path": request.url.path}
    )


class RouteRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    user_context: Optional[str] = None

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Query must not be empty.")
        return trimmed

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    from services.document_parser import extract_text_from_upload
    text = await extract_text_from_upload(file)
    if not text:
        raise HTTPException(status_code=400, detail="Could not extract text from file. Ensure it is a valid PDF or TXT.")
    return {"text": text}


@app.get("/")
def root() -> dict:
    return {
        "service": app.title,
        "status": "ok",
        "health": "/api/health",
        "route": "/api/route",
        "docs": "/docs",
    }


@app.get("/api/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "llm_provider": settings.llm_provider,
        "model": settings.openai_model,
        "langsmith_project": settings.langsmith_project,
    }


@app.post("/api/route", response_model=RouterResponse)
async def route_query(payload: RouteRequest) -> RouterResponse:
    try:
        logger.info("Incoming route request", extra={"query_length": len(payload.query)})
        state = run_router(payload.query, settings=settings, user_context=payload.user_context)
        response = state["response"]
        classification = state["classification"]
        safety_flags = state["safety_flags"]
        return RouterResponse(
            response=response.content,
            classification=classification,
            disclaimers=response.disclaimers + response.safety_notes,
            safety_flags=safety_flags,
            request_id=state.get("request_id", "unknown"),
            sources=response.sources,
            pipeline_trace=state.get("pipeline_trace", []),
        )
    except Exception as exc:
        logger.exception("Routing failed")
        raise HTTPException(status_code=500, detail="Routing failed") from exc
