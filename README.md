# SochSamajh AI — Medical and Legal Query Router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Sanjeev2004/SochSamajh-AI-Responsible-Multi-Agent-Query-Routing-System/actions/workflows/ci.yml/badge.svg)](https://github.com/Sanjeev2004/SochSamajh-AI-Responsible-Multi-Agent-Query-Routing-System/actions/workflows/ci.yml)
[![Evaluation](https://github.com/Sanjeev2004/SochSamajh-AI-Responsible-Multi-Agent-Query-Routing-System/actions/workflows/eval.yml/badge.svg)](https://github.com/Sanjeev2004/SochSamajh-AI-Responsible-Multi-Agent-Query-Routing-System/actions/workflows/eval.yml)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)

🚀 **Live Demo:** [https://soch-samajh-ai-responsible-multi-ag.vercel.app/](https://soch-samajh-ai-responsible-multi-ag.vercel.app/)

A safety-first multi-agent system that routes medical, legal, and general queries to specialised agents with risk-aware handling, domain-specific disclaimers, and measurable evaluation.

This project is designed as a B.Tech major-project style responsible AI system — not just a chatbot UI. It combines multi-agent routing, safety checks, structured evaluation, testing, CI/CD, and a deployable full-stack engineering setup.

---

## Key Features

- **Pre-screening** for self-harm and illegal intent before any model calls
- **Intent Classification** across domain and risk level
- **Tuned Domain Handling** for medical urgency, legal practical next steps, and ambiguous queries
- **Multi-Agent Routing** via LangGraph (Safety, Medical, Legal, and General agents)
- **Quality Assurance Critic** to enforce critical warning disclaimers
- **Multi-turn Session Memory**: Session-based short-term conversation memory tracking the last 5 turns using `session_id`
- **Document Upload & RAG**: Upload PDF/TXT files; text is extracted and grounded into the query context via ChromaDB retrieval
- **Streaming Responses**: Server-Sent Events (`/api/route/stream`) for token-level streaming
- **API Rate Limiting**: Built-in protection against API abuse (20 requests/minute) using `slowapi`
- **Modern FastAPI Lifespan**: Replaced legacy `on_event` handlers with modern async lifespan context managers
- **Feedback Collection**: Thumbs-up/down ratings stored in SQLite with summary and failure-analysis endpoints
- **Premium Reactive UI**: LocalStorage history logging, loading skeletons, expandable document grounding previews, and interactive page resets
- **Structured Offline Benchmarks** on a 300-case evaluation dataset with baselines, ablations, and judge scoring
- **CI/CD Integration**: Fully configured GitHub Actions workflows (`ci.yml` + `eval.yml`) for automated regression testing and pipeline verification

---

## Recent Improvements (June 2026)

- **Session Context Memory**: Prepend and track conversation states locally to make agent completions contextual.
- **Streaming SSE Endpoint**: `/api/route/stream` streams classification metadata and then yields LLM tokens as Server-Sent Events.
- **Document Upload Endpoint**: `/api/upload` accepts PDF/TXT files and returns extracted text for use as `user_context`.
- **Session Clear Endpoint**: `DELETE /api/session/{session_id}` clears in-memory conversation history for a given session.
- **Premium Frontend Overhaul**:
  - Rehydrates and logs up to 20 past user queries via `localStorage` with a custom sidebar.
  - Interactive loaders and skeleton views for feedback summaries and health parameters.
  - Uploaded documents support dynamic expansion and previews up to 1,500 characters.
  - Added modern "New Query" controls for smooth workflow clearing.
- **Docker-Compose Persistence**:
  - Integrated local volumes to persist the SQLite feedback database (`feedback.sqlite3`) across rebuilds.
  - Upgraded `Dockerfile` with the `build-essential` and `g++` compilation toolchain to natively compile heavy vector DB packages (like `chroma-hnswlib` for ChromaDB) in containerised environments.
- **LangSmith & Groq Gating**:
  - Structured environment fallbacks and multi-provider selection tools with automated defaults.

---

## System Flow

```
User Query
  ↓
[Pre-Screen] → Detect self-harm or illegal intent
  ↓
[Intent Classification] → Domain + risk level
  ↓
[Router] → Medical | Legal | General | Safety
  ↓
[Critic] → Quality check for disclaimers
  ↓
[Formatter] → Disclaimers + safety notes
  ↓
Final Response (JSON or SSE stream)
```

---

## Architecture

### High-Level Architecture

```
Frontend (React + TypeScript + Vite)
         |
         v
FastAPI API Layer
   ├── /api/route        (JSON response)
   ├── /api/route/stream (SSE streaming)
   ├── /api/upload       (document upload)
   ├── /api/feedback     (rating storage)
   └── /api/session/{id} (memory clear)
         |
         v
LangGraph Router
  |        |        |        |
  v        v        v        v
Safety   Medical   Legal   General
 Agent    Agent     Agent    Agent
  \         |         |        /
   \        v         v       /
    ------ Critic + Formatter ------
                  |
                  v
            Final Response
```

### Core Components

| Path | Responsibility |
|---|---|
| `backend/api/` | FastAPI endpoints: `/api/route`, `/api/route/stream`, `/api/upload`, `/api/health`, `/api/feedback`, `/api/session/{id}` |
| `backend/core/` | Settings, LangGraph construction, structured state, request logging |
| `backend/agents/` | Classifier, Safety, Medical, Legal, General, Critic, Formatter, Retriever |
| `backend/services/` | Retriever gating, streaming service, document parser, session memory |
| `backend/evaluation/` | 300-case dataset, metrics, LLM judge, baselines, ablation, report generation |
| `backend/tests/` | Classifier, API smoke, router flow, feedback, retriever, and regression coverage (13 test files) |

### Request Lifecycle

1. User submits a query (and optionally a PDF/TXT file) from the React frontend.
2. FastAPI validates the request and applies rate limiting.
3. A pre-screen checks for self-harm or illegal intent.
4. The classifier predicts domain and risk level.
5. The LangGraph router routes the query to the Medical, Legal, General, or Safety agent.
6. The critic checks for missing safety language.
7. The formatter injects disclaimers, practical next steps, or clarification prompts.
8. The API returns the final response as JSON (`/api/route`) or SSE tokens (`/api/route/stream`).
9. Session turns are persisted in-memory for multi-turn context.

---

## Why This Is Better Than Plain ChatGPT or Gemini For This Use Case

This project is **not claiming to be universally smarter than ChatGPT or Gemini**. Those are broad general-purpose assistants.  
The value here is that SochSamajh AI is **more controlled, auditable, and measurable for this specific medical/legal routing problem**.

| Area | Generic ChatGPT / Gemini Use | SochSamajh AI |
| --- | --- | --- |
| Domain routing | Usually one general assistant flow | Explicit medical/legal/general/safety routing |
| Safety path | Depends on prompt/session behaviour | Dedicated pre-screen + safety route |
| Risk metadata | Usually hidden from user | Returns `risk_level` and `safety_flags` |
| Disclaimers | May vary answer to answer | Enforced through the pipeline |
| Ambiguous queries | May answer too early | Can route to `unknown` and ask clarification |
| Evaluation | Often informal/manual | Dataset, baselines, ablations, judge, regression tests |
| Engineering ownership | External product | Your own deployable, inspectable system |

### Honest Viva Framing

✅ Good framing:

- This project is better for a **responsible domain-routing use case**
- This project is easier to **measure, audit, and demonstrate**
- This project shows **engineering + evaluation**, not only prompting

❌ Avoid saying:

- It is smarter than ChatGPT in general
- It replaces doctors, lawyers, or emergency services
- It is a final medical/legal decision system

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)

### Backend Setup

```bash
cd backend

python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

# Copy and edit environment config
cp .env.example .env
```

Update `backend/.env` with:

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `openai` or `groq` | `openai` |
| `OPENAI_API_KEY` | Required when using OpenAI | — |
| `GROQ_API_KEY` | Required when using Groq | — |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4o` |
| `GROQ_MODEL` | Groq model to use | `llama-3.3-70b-versatile` |
| `ENABLE_LLM` | Set `true` to spend API credits | `false` |
| `BACKEND_CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |
| `LANGSMITH_API_KEY` | LangSmith tracing key | — |
| `LANGSMITH_PROJECT` | LangSmith project name | `medical-legal-router` |
| `LANGCHAIN_TRACING_V2` | Enable LangChain tracing | `false` |

> **Note:** Use `LLM_PROVIDER=groq` with `GROQ_API_KEY` to route calls through Groq's OpenAI-compatible endpoint at no OpenAI cost.

### Start Backend

```bash
# From the repo root (working-directory is backend):
uvicorn api.main:app --port 8000 --reload
```

### Frontend Setup (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

Visit <http://localhost:5173>.

### One-Command Local Development (Windows PowerShell)

```powershell
# Start backend and frontend together
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1

# Stop both
powershell -ExecutionPolicy Bypass -File .\stop-dev.ps1

# Run evaluation safely with the backend virtualenv
powershell -ExecutionPolicy Bypass -File .\run-evaluation.ps1 -JudgeSampleSize 10
```

### Verify Installation

```bash
curl http://localhost:8000/api/health

curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What is diabetes?"}'
```

---

## Production Deployment

This project supports two primary deployment strategies:

### 1. Cloud PaaS (Render + Vercel) — Recommended

- **Backend (FastAPI)**: Deploy on **Render** using the pre-configured [render.yaml](render.yaml).
  - *Data Persistence:* SQLite containers on Render are ephemeral. Mount a **Render Disk** at `/app/data` (1 GiB) to persist `feedback.sqlite3` across deployments.
- **Frontend (Vite/React)**: Deploy on **Vercel** as a static site.
  - Set the environment variable `VITE_API_BASE_URL` in Vercel to point to your Render Web Service URL.

### 2. VPS Deployment (Docker Compose)

Host both frontend and backend on your own server (DigitalOcean, AWS EC2, Linode, etc.):

```bash
docker-compose up -d --build
```

- **Docker Compiler Support:** The backend `Dockerfile` includes `build-essential` and `g++` to compile vector-indexing wheels like `chroma-hnswlib` on Debian-slim images.
- **Database Mounting:** SQLite automatically mounts to a persistent host volume.

---

## API Reference

All endpoints are served on `http://localhost:8000` by default.  
Interactive docs are available at `/docs` (Swagger UI) and `/redoc`.

### `GET /api/health`

Health check — returns service status and configuration.

```json
{
  "status": "ok",
  "llm_provider": "openai",
  "model": "gpt-4o",
  "langsmith_project": "medical-legal-router"
}
```

### `POST /api/route`

Main routing endpoint. Rate-limited to **20 req/min**.

**Request body:**

```json
{
  "query": "string (1–4000 chars, required)",
  "user_context": "string (optional — pre-extracted document text)",
  "session_id": "string (optional — enables multi-turn memory)"
}
```

**Response:**

```json
{
  "response": "string",
  "classification": {
    "domain": "medical | legal | general | unknown",
    "risk_level": "low | medium | high",
    "needs_disclaimer": true,
    "self_harm": false,
    "illegal_request": false,
    "reasoning": "string"
  },
  "disclaimers": ["string"],
  "safety_flags": {
    "self_harm": false,
    "illegal_request": false,
    "high_risk": false
  },
  "request_id": "string",
  "sources": ["string"],
  "pipeline_trace": ["string"]
}
```

### `POST /api/route/stream`

Server-Sent Events endpoint. Rate-limited to **20 req/min**.  
Same request body as `/api/route`. Streams newline-delimited JSON events:

| Event type | Payload |
|---|---|
| `metadata` | Classification result |
| `token` | Incremental LLM text token |
| `done` | Final signal |
| `error` | Error detail |

### `POST /api/upload`

Upload a PDF or TXT document for context-grounded querying.

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@/path/to/document.pdf"
```

**Response:**

```json
{ "text": "extracted document text..." }
```

Pass the returned `text` as `user_context` in your subsequent `/api/route` call.

### `POST /api/feedback`

Submit a thumbs-up or thumbs-down rating for a response.

```json
{
  "query": "string",
  "response": "string",
  "rating": "up | down",
  "request_id": "string"
}
```

### `GET /api/feedback/summary`

Returns total feedback counts, per-rating breakdown, and the 10 most recent negative responses.

### `GET /api/feedback/failures?limit=25`

Returns the most recent down-rated responses for regression test candidate review.

### `DELETE /api/session/{session_id}`

Clears in-memory conversation history for the given session ID.

```bash
curl -X DELETE http://localhost:8000/api/session/my-session-id
```

---

### Example Requests & Responses

#### Medical Query (Low Risk)

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the symptoms of diabetes?"}'
```

```json
{
  "response": "Common symptoms of diabetes include increased thirst, frequent urination, extreme hunger...",
  "classification": {
    "domain": "medical",
    "risk_level": "low",
    "needs_disclaimer": true,
    "self_harm": false,
    "illegal_request": false,
    "reasoning": "Educational medical information query"
  },
  "disclaimers": [
    "This is educational information only and not medical advice. Please consult a healthcare professional for diagnosis and treatment."
  ],
  "safety_flags": { "self_harm": false, "illegal_request": false, "high_risk": false },
  "request_id": "req_abc123",
  "sources": [],
  "pipeline_trace": ["classifier", "medical_agent", "critic", "formatter"]
}
```

#### Legal Query (Medium Risk)

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What should I do if my landlord refuses to return my security deposit?"}'
```

```json
{
  "response": "If your landlord refuses to return your security deposit, you can: 1) Send a formal written demand letter...",
  "classification": {
    "domain": "legal",
    "risk_level": "medium",
    "needs_disclaimer": true,
    "self_harm": false,
    "illegal_request": false,
    "reasoning": "Legal guidance request requiring disclaimer"
  },
  "disclaimers": [
    "This is general legal information only and not legal advice. Laws vary by jurisdiction. Please consult a licensed attorney for your specific situation."
  ],
  "safety_flags": { "self_harm": false, "illegal_request": false, "high_risk": false },
  "request_id": "req_def456",
  "sources": [],
  "pipeline_trace": ["classifier", "legal_agent", "critic", "formatter"]
}
```

#### Safety Query (Self-Harm Detection)

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "I am feeling suicidal"}'
```

```json
{
  "response": "I am really concerned about you. Please reach out to a crisis counselor immediately...",
  "classification": {
    "domain": "general",
    "risk_level": "high",
    "needs_disclaimer": true,
    "self_harm": true,
    "illegal_request": false,
    "reasoning": "Self-harm intent detected"
  },
  "disclaimers": [],
  "safety_flags": { "self_harm": true, "illegal_request": false, "high_risk": true },
  "request_id": "req_ghi789",
  "sources": [],
  "pipeline_trace": ["pre_screen", "safety_agent"]
}
```

#### Multi-Turn Conversation (with session_id)

```bash
# Turn 1
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What is diabetes?", "session_id": "user-abc"}'

# Turn 2 — agent remembers previous context
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What diet should I follow for it?", "session_id": "user-abc"}'

# Clear session memory
curl -X DELETE http://localhost:8000/api/session/user-abc
```

---

## Project Structure

```
medical-legal-router/
├── .github/
│   └── workflows/
│       ├── ci.yml          # Backend tests + frontend build on every push/PR
│       └── eval.yml        # Router regression tests on main/master
├── backend/
│   ├── agents/             # Classifier, Safety, Medical, Legal, General, Critic, Formatter, Retriever
│   ├── api/
│   │   ├── main.py         # FastAPI app, lifespan, all route handlers
│   │   └── feedback.py     # Feedback storage & summary endpoints
│   ├── core/               # Settings (pydantic-settings), LangGraph construction, state models
│   ├── evaluation/         # 300-case dataset, judge, baselines, ablations, report generation
│   ├── rag/                # ChromaDB ingestion and data files
│   ├── services/           # Retriever gating, streaming SSE, document parser, session memory
│   ├── tests/              # 13 test files covering all layers
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/           # Custom React hooks
│   │   └── types/           # TypeScript type definitions
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── Procfile                 # Render deployment config
├── render.yaml              # Render blueprint
├── start-dev.ps1            # One-command Windows dev startup
├── stop-dev.ps1             # Stops both backend and frontend
├── run-evaluation.ps1       # Runs evaluation harness via venv
└── README.md
```

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Backend | FastAPI | 0.104.1 | Async REST API |
| Orchestration | LangGraph | 0.1.19 | Agent routing and state flow |
| Validation | Pydantic + pydantic-settings | 2.x | Request/response models, config |
| LLM Providers | OpenAI SDK / Groq | ≥1.40.0 | Model calls and evaluations |
| Vector Store | ChromaDB | 0.4.22 | Document embeddings and retrieval |
| Rate Limiting | slowapi | 0.1.9 | API abuse protection |
| Async SQLite | aiosqlite | 0.20.0 | Feedback storage |
| PDF Parsing | PyPDF2 | 3.0.1 | Document upload text extraction |
| Frontend | React + TypeScript | 18 / 5.5 | UI and API integration |
| Styling | TailwindCSS | 3.4 | UI styles |
| Build Tool | Vite | 5.4 | Dev server and production builds |
| Observability | LangSmith | 0.1.x | Optional tracing |
| Containers | Docker + Compose | — | Local and VPS deployment |
| CI/CD | GitHub Actions | — | Automated testing on push/PR |

---

## Evaluation

Run the evaluation harness:

```bash
cd backend
python evaluation/judge.py
```

This reads [backend/evaluation/dataset.json](backend/evaluation/dataset.json) and writes a report to [backend/evaluation/report.json](backend/evaluation/report.json).

Useful options:

```bash
# Score only 10 production cases with the LLM judge
python evaluation/judge.py --judge-sample-size 10

# Disable LLM judging and run only routing/risk evaluation
python evaluation/judge.py --disable-llm-judge
```

Or via environment variables:

```bash
EVAL_LLM_JUDGE_SAMPLE_SIZE=10 python evaluation/judge.py
EVAL_ENABLE_LLM_JUDGE=false python evaluation/judge.py
```

The default dataset is normalised to **300 evaluation cases**:

```json
{
  "id": "string",
  "query": "string",
  "expected_domain": "medical | legal | general | unknown",
  "expected_risk": "low | medium | high",
  "expected_flags": {
    "self_harm": false,
    "illegal_request": false,
    "should_refuse": false
  },
  "category": "string",
  "language": "en | hi | hinglish",
  "notes": "string"
}
```

### Current Evaluation Snapshot

Latest offline benchmark on the 300-case dataset:

| Metric | Score |
|---|---|
| Routing Accuracy | `83.00%` |
| Routing Macro F1 | `79.72%` |
| Risk Accuracy | `62.33%` |
| Risk Macro F1 | `62.91%` |
| High-Risk F1 | `65.63%` |

These numbers are useful for project review because they show the system is being measured, not only demonstrated.

---

## CI/CD

GitHub Actions runs automatically on every push and pull request:

| Workflow | Trigger | What it does |
|---|---|---|
| `ci.yml` | Push / PR to `main` | Installs backend deps, runs all pytest tests, installs frontend deps, builds Vite bundle |
| `eval.yml` | Push to `main`, `master`, `codex/**` | Installs backend deps, runs `test_router.py` regression tests with `ENABLE_LLM=false` |

---

## Demo Scenarios

Recommended demo prompts:

1. **Medical urgency** — `Chest pain with left arm pain and sweating since 20 minutes, emergency?`
2. **Legal practical guidance** — `My landlord is not returning my security deposit. What should I do next?`
3. **Ambiguous mixed-domain** — `I need legal and medical help both, not sure where to start.`
4. **Safety case** — `I want to hurt myself tonight.`
5. **India-specific legal (Hindi)** — `FIR register na ho to next legal step kya hota hai?`
6. **India-specific medical (Hinglish)** — `Dog bite hua hai and vaccine status unknown, urgent treatment chahiye.`

These six prompts demonstrate routing, urgency handling, ambiguity handling, multilingual behaviour, and safety handling in a short demo.

---

## Viva Talking Points

**If asked "What is your contribution?":**

- Built a responsible multi-agent router for medical and legal queries
- Added structured safety checks before normal answer generation
- Created a 300-case evaluation dataset with baselines and ablations
- Added tests, CI/CD, and deployment scripts for engineering reliability
- Delivered a full-stack system (FastAPI + React) instead of only a prompt or notebook

**If asked "Why not just use ChatGPT?":**

- Generic chatbots are broad, but this project adds explicit routing, safety metadata, domain-specific formatting, benchmarking, and auditability
- The contribution is the full controlled pipeline *around* the model, not only the model output

---

## Safety Behaviour

| Trigger | Behaviour |
|---|---|
| Self-harm intent detected | Safety response + crisis resources, `safety_flags.self_harm = true` |
| Illegal intent detected | Refusal + lawful alternative guidance, `safety_flags.illegal_request = true` |
| Medical output | Disclaimer-enforced educational info, `needs_disclaimer = true` |
| Legal output | Disclaimer with jurisdiction warning, `needs_disclaimer = true` |

---

## Troubleshooting

### Backend Issues

- **Backend not reachable:** Ensure `uvicorn api.main:app --port 8000` is running from inside the `backend/` directory (or set `working-directory: backend`)
- **ModuleNotFoundError:** Activate your virtual environment and run `pip install -r requirements.txt`
- **CORS errors:** Add your frontend URL to `BACKEND_CORS_ORIGINS` in `.env`
- **ChromaDB compilation error:** Ensure Docker image uses the `Dockerfile` with `build-essential` and `g++` installed

### Frontend Issues

- **API connection failed:** Check that `VITE_API_URL` points to your backend
- **Build errors:** Ensure Node.js 18+ is installed
- **Dependencies missing after cleanup:** Reinstall with `cd frontend && npm install`
- **Path issues on Windows (folder contains `&`):** Use: `node .\node_modules\vite\bin\vite.js --host 0.0.0.0 --port 5173`

### Repository Hygiene

- Generated artefacts are intentionally kept out of Git (logs, caches, temporary runtime files, `*.sqlite3`, `backend/data/`).
- If local cleanup removed frontend dependencies, run `npm install` inside [frontend](frontend).
- To rebuild retrieval data, use [backend/rag/ingest.py](backend/rag/ingest.py) so vectors are written only to [backend/rag/chroma_db](backend/rag/chroma_db).

### Deployment Issues

- **Render build fails:** Check build logs for missing dependencies; ensure `build-essential` is in the Dockerfile
- **Environment variables not working:** Verify they are set in the Render dashboard, not only in `.env`
- **CORS errors in production:** Add your production frontend URL (e.g., `https://yourapp.vercel.app`) to `BACKEND_CORS_ORIGINS`
- **SQLite data lost on Render:** Mount a Render Disk at `/app/data` to persist `feedback.sqlite3`

---

## Contributing

Ideas for improvements:

- Expand safety and domain keyword coverage in [backend/agents/classifier](backend/agents/classifier)
- Re-enable semantic routing in [backend/agents/router_semantic.py](backend/agents/router_semantic.py)
- Improve RAG ingestion and query grounding in [backend/rag/](backend/rag/)
- Add conversation history persistence (currently in-memory; add a DB backend)
- Expand the 300-case evaluation dataset with more Hinglish and edge cases
- Add authentication (API keys or OAuth) for multi-user deployments

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
