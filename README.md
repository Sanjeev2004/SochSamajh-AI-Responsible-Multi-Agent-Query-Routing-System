# SochSamajh AI — Responsible Multi-Agent Query Routing

> **Suggested GitHub description:** Safety-first FastAPI + LangGraph router that classifies medical/legal/general queries by domain and risk, with RAG grounding, explainable routing, and a 300-case evaluation suite.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Sanjeev2004/SochSamajh-AI-Responsible-Multi-Agent-Query-Routing-System/actions/workflows/ci.yml/badge.svg)](https://github.com/Sanjeev2004/SochSamajh-AI-Responsible-Multi-Agent-Query-Routing-System/actions/workflows/ci.yml)
[![Evaluation](https://github.com/Sanjeev2004/SochSamajh-AI-Responsible-Multi-Agent-Query-Routing-System/actions/workflows/eval.yml/badge.svg)](https://github.com/Sanjeev2004/SochSamajh-AI-Responsible-Multi-Agent-Query-Routing-System/actions/workflows/eval.yml)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)

**Live demo:** [https://soch-samajh-ai-responsible-multi-ag.vercel.app/](https://soch-samajh-ai-responsible-multi-ag.vercel.app/)

Safety-first multi-agent system that routes medical, legal, and general queries to specialised agents with risk-aware handling, domain disclaimers, explainable routing, and a measurable evaluation suite. Built as a B.Tech major-project style responsible AI system — not only a chatbot UI.

---

## What it does

- **Safety pre-screen** for self-harm and illegal intent before any model calls
- **Domain + risk classification** (medical / legal / general / unknown × low / medium / high)
- **LangGraph agents** — Safety, Medical, Legal, General → Critic → Formatter
- **Disclaimers & critic checks** so medical/legal answers stay educational and auditable
- **Eval + CI** — 300-case dataset, baselines/ablations, pytest (117+), GitHub Actions

---

## Highlights

| Area | What’s in place |
|---|---|
| **Risk scoring** | Separate medical-urgency vs legal high-risk paths; offline **risk accuracy ~76%** after Nov 2026 overhaul (was ~62%). Routing still **~83%**. |
| **Hybrid routing** | Keyword cascade + lazy semantic router (`router_semantic.py`) with India/Hinglish anchors; silent fallback if the embedding model fails |
| **Educational RAG** | Expanded medical/legal corpora; keyword/BM25-like fallback if Chroma/embeddings fail |
| **Explainability UI** | “Why this route?”, confidence, triggered terms, pipeline-trace chips |
| **Product features** | SSE streaming, PDF/TXT upload, thumbs feedback (SQLite), session memory (last 5 turns) |

---

## Architecture

```
Frontend (React + TypeScript + Vite)
              |
              v
        FastAPI API
   /api/route  /api/route/stream  /api/upload
   /api/feedback  /api/session/{id}  /api/health
              |
              v
     Pre-screen → Classifier (keyword + optional semantic)
              |
              v
         LangGraph Router
    Safety | Medical | Legal | General
              |
              v
       Critic → Formatter → Response (JSON or SSE)
```

**Request lifecycle**

1. Client sends a query (optional `user_context` / `session_id`; optional PDF/TXT via `/api/upload`).
2. Rate limit → pre-screen (self-harm / illegal).
3. Classifier predicts domain + risk (hybrid keyword + optional semantic).
4. LangGraph routes to the matching agent; critic checks safety language; formatter adds disclaimers.
5. Response returns as JSON or SSE; session turns kept in-memory for multi-turn context.

---

## Why not just ChatGPT?

Generic assistants are broad. SochSamajh AI is **controlled, auditable, and measurable** for medical/legal routing.

| Area | Generic ChatGPT / Gemini | SochSamajh AI |
|---|---|---|
| Domain routing | One general flow | Explicit medical / legal / general / safety |
| Safety path | Prompt-dependent | Dedicated pre-screen + safety agent |
| Risk metadata | Usually hidden | Returns `risk_level`, `safety_flags` |
| Disclaimers | Variable | Enforced by critic + formatter |
| Ambiguity | May answer early | Can route `unknown` and ask to clarify |
| Evaluation | Informal | 300-case dataset, baselines, ablations, CI |

---

## Quick start

**Prerequisites:** Python 3.11+, Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
```

| Variable | Description | Default / notes |
|---|---|---|
| `LLM_PROVIDER` | `groq` (recommended) or `openai` | `groq` in `.env.example` |
| `GROQ_API_KEY` | Groq API key | required when using Groq |
| `GROQ_MODEL` | Groq model | `llama-3.3-70b-versatile` |
| `OPENAI_API_KEY` | OpenAI key (if using OpenAI) | — |
| `ENABLE_LLM` | Live LLM calls (`true` spends credits) | `false` |
| `ENABLE_RETRIEVER` | Chroma / keyword RAG | `false` |
| `ENABLE_SEMANTIC_ROUTER` | Hybrid semantic cascade | `false` |
| `BACKEND_CORS_ORIGINS` | Allowed origins (comma-separated) | `http://localhost:5173` |

```bash
# From backend/
uvicorn api.main:app --port 8000 --reload
```

### Rebuild Chroma (after editing RAG text)

```bash
cd backend
python -m rag.ingest
```

Rewrites `backend/rag/chroma_db/`. Set `ENABLE_RETRIEVER=true` to use retrieval. If sentence-transformers/Chroma cannot load, the retriever falls back to an in-process keyword scorer over the same `.txt` files.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>.

**Windows one-command:** `powershell -ExecutionPolicy Bypass -File .\start-dev.ps1`

**Smoke check:**

```bash
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What is diabetes?"}'
```

### Deploy (short)

- **Backend:** Render via [`render.yaml`](render.yaml); mount a disk at `/app/data` if you need persistent SQLite feedback.
- **Frontend:** Vercel; set `VITE_API_BASE_URL` to the Render URL.
- **VPS:** `docker-compose up -d --build`

---

## API reference

Base: `http://localhost:8000` — interactive docs at `/docs`.

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/health` | Status, provider, model |
| `POST` | `/api/route` | Main JSON route (20 req/min) |
| `POST` | `/api/route/stream` | SSE: `metadata` → `token` → `done` |
| `POST` | `/api/upload` | PDF/TXT → `{ "text": "..." }` for `user_context` |
| `POST` | `/api/feedback` | `{ query, response, rating: "up"|"down", request_id }` |
| `GET` | `/api/feedback/summary` | Counts + recent downs |
| `GET` | `/api/feedback/failures` | Down-rated samples for regression review |
| `DELETE` | `/api/session/{session_id}` | Clear in-memory session |

**Route body:** `{ "query": "...", "user_context"?: "...", "session_id"?: "..." }`

**Route response (shape):** `response`, `classification` (`domain`, `risk_level`, flags, `reasoning`), `disclaimers`, `safety_flags`, `request_id`, `sources`, `pipeline_trace`.

### Examples

**Medical (low risk)**

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the symptoms of diabetes?"}'
# → domain: medical, needs_disclaimer: true, pipeline includes medical_agent
```

**Safety (self-harm)**

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "I am feeling suicidal"}'
# → pre_screen → safety_agent; safety_flags.self_harm: true
```

---

## Project structure

```
sochsamajh/
├── .github/workflows/     # ci.yml, eval.yml
├── backend/
│   ├── agents/            # classifier/, safety, medical, legal, general,
│   │                      # critic, formatter, retriever, router_semantic
│   ├── api/               # main.py, feedback.py
│   ├── core/              # config, LangGraph, state
│   ├── evaluation/        # dataset.json (300), judge, metrics, visualizations
│   ├── rag/               # ingest.py, data/*.txt, chroma_db/
│   ├── services/          # retrieval, streaming, document_parser, memory
│   ├── tests/             # 14 test modules (117+ tests)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/               # App, components, hooks, types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── render.yaml
├── Procfile
└── README.md
```

---

## Tech stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend | FastAPI 0.104 | Async REST + SSE |
| Orchestration | LangGraph 0.1.19 | Multi-agent state flow |
| Config / models | Pydantic + pydantic-settings | Validation & settings |
| LLM | OpenAI SDK / Groq | Completions & judge |
| RAG | ChromaDB + sentence-transformers | Embeddings + keyword fallback |
| Rate limit | slowapi | 20 req/min on route |
| Feedback DB | aiosqlite | Thumbs up/down |
| Upload | PyPDF2 | PDF text extraction |
| Frontend | React 18 + TypeScript + Vite + Tailwind | UI |
| Observability | LangSmith (optional) | Tracing |
| CI/CD | GitHub Actions | pytest + frontend build |

---

## Evaluation

```bash
cd backend
python evaluation/judge.py
# python evaluation/judge.py --judge-sample-size 10
# python evaluation/judge.py --disable-llm-judge
```

Writes `backend/evaluation/report.json` from the **300-case** dataset (`dataset.json`).

### Offline snapshot (current main)

| Metric | Score |
|---|---|
| Routing accuracy | **~83%** |
| Routing macro F1 | **~79.7%** |
| Risk accuracy | **~76%** (post Nov 2026 scoring overhaul; previously ~62%) |
| Dataset | 300 cases + baselines / ablations |
| Tests | **117+** pytest cases in CI |

`ci.yml` runs the full backend test suite + frontend build on push/PR. `eval.yml` runs router regression tests with `ENABLE_LLM=false`.

---

## Demo scenarios

1. **Medical urgency** — `Chest pain with left arm pain and sweating since 20 minutes, emergency?`
2. **Legal next steps** — `My landlord is not returning my security deposit. What should I do next?`
3. **Ambiguous mixed-domain** — `I need legal and medical help both, not sure where to start.`
4. **Safety** — `I want to hurt myself tonight.`
5. **India legal (Hindi)** — `FIR register na ho to next legal step kya hota hai?`
6. **India medical (Hinglish)** — `Dog bite hua hai and vaccine status unknown, urgent treatment chahiye.`

---

## Viva talking points

- **Contribution:** End-to-end responsible router (pre-screen → classify → agents → critic → disclaimers), not only a prompt or notebook.
- **Why not ChatGPT alone:** Explicit routing, safety flags, enforced disclaimers, explainability UI, and a 300-case measurable eval suite.
- **Evidence:** ~83% routing / ~76% risk offline; 117+ tests; CI/CD; deployable FastAPI + React stack.
- **Design choices:** Hybrid keyword + semantic routing for India/Hinglish; RAG with keyword fallback; session memory and feedback for iteration.

---

## Safety behaviour

| Trigger | Behaviour |
|---|---|
| Self-harm intent | Crisis-oriented safety response; `safety_flags.self_harm = true` |
| Illegal intent | Refusal + lawful alternatives; `safety_flags.illegal_request = true` |
| Medical output | Educational info + enforced disclaimer |
| Legal output | General information + jurisdiction disclaimer |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `401 expired_api_key` / Invalid API Key | Refresh `OPENAI_API_KEY` or `GROQ_API_KEY` on Render (or local `.env`) and set `ENABLE_LLM=true` |
| Backend unreachable | Run `uvicorn api.main:app --port 8000` from `backend/` |
| `ModuleNotFoundError` | Activate venv; `pip install -r requirements.txt` |
| CORS errors | Add frontend origin to `BACKEND_CORS_ORIGINS` |
| Frontend can’t reach API | Set `VITE_API_BASE_URL` / `VITE_API_URL` to the backend URL |
| Chroma build fails in Docker | Use backend `Dockerfile` (includes `build-essential` / `g++`) |
| SQLite lost on Render | Mount a Render Disk at `/app/data` |

---

## Contributing / next steps

- Persist session memory beyond in-process store (DB-backed)
- Human evaluation pass on the 300-case set
- Run `python -m rag.ingest` in deploy so Chroma is warm in production
- Optional auth (API keys / OAuth) for multi-user deployments
- Expand Hinglish / edge-case coverage in the dataset and classifier keywords

---

## License

MIT — see [LICENSE](LICENSE).
