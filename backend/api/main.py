import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from core.config import Settings, logger
from core.graph import run_router
from core.state import RouterResponse
from api.feedback import router as feedback_router, _ensure_db
from services.memory_service import memory

settings = Settings.load()

# ── Rate limiter (improvement #6) ─────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/hour"])


# ── Lifespan (improvement #4 — replaces deprecated @app.on_event) ─────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──
    # 1. Initialise feedback DB
    await _ensure_db()
    logger.info("Feedback database initialised")

    # 2. Warm up retriever in background
    async def _warmup() -> None:
        try:
            from agents.retriever import retriever
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, retriever._initialize)
            logger.info("Retriever warmed up on startup")
        except Exception:
            logger.exception("Retriever warmup failed — continuing without it")

    asyncio.create_task(_warmup())
    yield
    # ── Shutdown ── (nothing to clean up currently)


app = FastAPI(
    title="Medical and Legal Query Router",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(feedback_router)

allow_credentials = True
if "*" in settings.backend_cors_origins:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error for {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "path": request.url.path,
        },
    )


# ── Request models ─────────────────────────────────────────────────────────────

class RouteRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    user_context: Optional[str] = None
    session_id: Optional[str] = None  # improvement #3: conversation memory

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Query must not be empty.")
        return trimmed


# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_context(payload: RouteRequest) -> str | None:
    """Merge document context with conversation history when session_id provided."""
    if not payload.session_id:
        return payload.user_context

    history_ctx = memory.get_context(payload.session_id)
    if not history_ctx:
        return payload.user_context

    doc_ctx = payload.user_context or ""
    return (
        f"Conversation history (last {5} turns):\n{history_ctx}\n\n"
        f"Current document context:\n{doc_ctx}"
    ).strip()


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
    from services.document_parser import extract_text_from_upload
    text = await extract_text_from_upload(file)
    if not text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from file. Ensure it is a valid PDF or TXT.",
        )
    return {"text": text}


@app.get("/")
def root() -> dict:
    return {
        "service": app.title,
        "status": "ok",
        "health": "/api/health",
        "route": "/api/route",
        "stream": "/api/route/stream",
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
@limiter.limit("20/minute")
async def route_query(request: Request, payload: RouteRequest) -> RouterResponse:
    try:
        logger.info("Incoming route request | len=%d", len(payload.query))
        combined_context = _build_context(payload)
        state = run_router(payload.query, settings=settings, user_context=combined_context)
        response = state["response"]
        classification = state["classification"]
        safety_flags = state["safety_flags"]

        # Store turns in memory for multi-turn sessions (#3)
        if payload.session_id:
            memory.add_turn(payload.session_id, "user", payload.query)
            memory.add_turn(payload.session_id, "assistant", response.content[:800])

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


@app.post("/api/route/stream")
@limiter.limit("20/minute")
async def route_query_stream(request: Request, payload: RouteRequest) -> StreamingResponse:
    """Server-Sent Events endpoint.

    Streams classification metadata immediately, then yields LLM tokens.
    Events are newline-delimited JSON with a 'type' field:
      metadata | token | done | error
    """
    from services.streaming_service import build_sse_stream

    combined_context = _build_context(payload)

    def _sync_gen():
        yield from build_sse_stream(
            query=payload.query,
            settings=settings,
            user_context=combined_context,
        )

    async def _async_gen():
        full_text_parts: list[str] = []
        loop = asyncio.get_running_loop()
        gen = _sync_gen()
        while True:
            chunk = await loop.run_in_executor(None, lambda: next(gen, None))
            if chunk is None:
                break
            yield chunk

        # After stream ends, persist turns to memory
        if payload.session_id:
            memory.add_turn(payload.session_id, "user", payload.query)

    logger.info("Incoming stream request | len=%d", len(payload.query))
    return StreamingResponse(
        _async_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@app.delete("/api/session/{session_id}")
def clear_session(session_id: str) -> dict:
    """Clear conversation memory for the given session (improvement #3)."""
    memory.clear(session_id)
    return {"cleared": session_id}
