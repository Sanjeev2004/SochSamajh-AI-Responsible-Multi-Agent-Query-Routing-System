# SochSamajh AI - Medical and Legal Query Router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)

A safety-first multi-agent system that routes medical, legal, and general queries to specialized agents with risk-aware handling, domain-specific disclaimers, and measurable evaluation.

This project is designed as a B.Tech major-project style responsible AI system, not just a chatbot UI. It combines multi-agent routing, safety checks, structured evaluation, testing, CI, and deployable full-stack engineering.

## Key Features

- Pre-screening for self-harm and illegal intent before model calls
- Intent classification across domain and risk level
- Better handling for medical urgency, legal practical-next-step queries, and ambiguous mixed-domain prompts
- Dedicated agents for medical, legal, general, and safety responses
- LangGraph-based routing with critic and formatter stages
- Structured evaluation on a 300-case dataset with baselines and ablations
- Fix-driven regression testing on real prompts (including Hinglish/India-specific phrasing)
- Backend tests, CI, and local dev/evaluation scripts
- FastAPI backend and React + TypeScript frontend

## Recent Improvements (March 2026)

- Classifier tuning:
  - stronger medical urgency detection (for example chest tightness, breathing difficulty, stroke-like symptoms)
  - better legal intent detection for practical process questions (documents, complaint flow, legal notice)
  - improved unknown/ambiguous routing when users ask for guidance without enough context
- Response quality tuning:
  - high-risk medical responses now include immediate action guidance
  - medium/high legal responses include practical next-step checklists
  - unknown-domain responses ask focused clarification questions instead of guessing too early
- RAG stability fix:
  - ingestion now uses file-relative paths to avoid accidental nested duplicate folders
  - canonical RAG location remains under [backend/rag](backend/rag)
- Regression coverage:
  - added fix-driven test prompts to prevent backsliding in urgency, legal-process, and ambiguity behavior

## System Flow

```
User Query
  ↓
[Pre-Screen] → Detect self-harm or illegal intent
  ↓
[Intent Classification] → Domain + risk
  ↓
[Router] → Medical | Legal | General | Safety
  ↓
[Critic] → Quality check
  ↓
[Formatter] → Disclaimers + safety notes
  ↓
Final Response
```

## Why This Project Matters

Medical and legal questions are high-stakes because generic answers can be confusing, unsafe, or overconfident. This project tries to solve that by:

- separating domain routing from answer generation
- treating urgent and harmful cases differently from normal questions
- attaching structured safety metadata to responses
- evaluating the system with repeatable offline benchmarks instead of only manual demos

## Architecture

### High-Level Architecture

```
Frontend (React + TypeScript)
        |
        v
FastAPI API Layer
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

- `backend/api/`
  FastAPI endpoints such as `/api/route`, `/api/health`, and `/api/feedback`
- `backend/core/`
  settings, graph construction, structured state, and request logging
- `backend/agents/`
  classifier, safety, medical, legal, general, critic, formatter, and retriever logic
- `backend/services/`
  service helpers such as retriever gating
- `backend/evaluation/`
  dataset, metrics, judge, baselines, ablation logic, and report generation
- `backend/tests/`
  classifier, API, router-flow, feedback, retriever, and regression coverage

### Request Lifecycle

1. User submits a query from the React frontend.
2. FastAPI validates the request.
3. A pre-screen checks for self-harm or illegal intent.
4. The classifier predicts domain and risk.
5. The graph routes the query to medical, legal, general, or safety handling.
6. The critic checks for missing safety language.
7. The formatter injects disclaimers, practical next steps, or clarification prompts.
8. The API returns the final response with metadata and safety flags.

## Why This Is Better Than Plain ChatGPT or Gemini For This Use Case

This project is **not claiming to be universally smarter than ChatGPT or Gemini**. Those are broad general-purpose assistants.  
The value here is that SochSamajh AI is **more controlled, auditable, and measurable for this specific medical/legal routing problem**.

| Area | Generic ChatGPT / Gemini Use | SochSamajh AI |
| --- | --- | --- |
| Domain routing | Usually one general assistant flow | Explicit medical/legal/general/safety routing |
| Safety path | Depends on prompt/session behavior | Dedicated pre-screen + safety route |
| Risk metadata | Usually hidden from user | Returns `risk_level` and `safety_flags` |
| Disclaimers | May vary answer to answer | Enforced through the pipeline |
| Ambiguous queries | May answer too early | Can route to `unknown` and ask clarification |
| Evaluation | Often informal/manual | Dataset, baselines, ablations, judge, regression tests |
| Engineering ownership | External product | Your own deployable, inspectable system |

### Honest Viva Framing

Good framing:

- this project is better for a **responsible domain-routing use case**
- this project is easier to **measure, audit, and demonstrate**
- this project shows **engineering + evaluation**, not only prompting

Avoid saying:

- it is smarter than ChatGPT in general
- it replaces doctors, lawyers, or emergency services
- it is a final medical/legal decision system

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)

### Backend Setup

```bash
cd backend

python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt

# Environment
cp .env.example .env
```

Update `backend/.env` with:

- `OPENAI_API_KEY` (required)
- `OPENAI_MODEL` (optional, default is `gpt-4o`)
- `BACKEND_CORS_ORIGINS` (optional, comma-separated)

**Note:** The `.env.example` includes both OpenAI and OpenRouter configurations. Use OpenAI variables for standard deployment, or uncomment OpenRouter variables if using that service.

### Start Backend

```bash
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

Start backend and frontend together:

```powershell
powershell -ExecutionPolicy Bypass -File .\start-dev.ps1
```

Stop both:

```powershell
powershell -ExecutionPolicy Bypass -File .\stop-dev.ps1
```

Run evaluation safely with the backend virtualenv:

```powershell
powershell -ExecutionPolicy Bypass -File .\run-evaluation.ps1 -JudgeSampleSize 10
```

### Verify Installation

```bash
curl http://localhost:8000/api/health

curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What is diabetes?"}'
```

## API Reference

### `GET /api/health`

Health check endpoint that returns service status and configuration.

**Response:**

```json
{
  "status": "ok",
  "model": "gpt-4o",
  "langsmith_project": "medical-legal-router"
}
```

### `POST /api/route`

Main routing endpoint that processes queries through the multi-agent system.

**Request Body:**

```json
{
  "query": "string (1-4000 characters, required)"
}
```

**Response Model:**

```json
{
  "response": "string",
  "classification": {
    "domain": "medical | legal | general",
    "risk_level": "low | medium | high",
    "needs_disclaimer": "boolean",
    "self_harm": "boolean",
    "illegal_request": "boolean",
    "reasoning": "string"
  },
  "disclaimers": ["string"],
  "safety_flags": {
    "self_harm": "boolean",
    "illegal_request": "boolean",
    "high_risk": "boolean"
  },
  "request_id": "string"
}
```

### Example Requests & Responses

#### Medical Query (Low Risk)

**Request:**

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the symptoms of diabetes?"}'
```

**Response:**

```json
{
  "response": "Common symptoms of diabetes include increased thirst, frequent urination, extreme hunger, unexplained weight loss, fatigue, blurred vision, slow-healing sores, and frequent infections...",
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
  "safety_flags": {
    "self_harm": false,
    "illegal_request": false,
    "high_risk": false
  },
  "request_id": "req_abc123"
}
```

#### Legal Query (Medium Risk)

**Request:**

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What should I do if my landlord refuses to return my security deposit?"}'
```

**Response:**

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
  "safety_flags": {
    "self_harm": false,
    "illegal_request": false,
    "high_risk": false
  },
  "request_id": "req_def456"
}
```

#### Safety Query (Self-Harm Detection)

**Request:**

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "I am feeling suicidal"}'
```

**Response:**

```json
{
  "response": "I'm really concerned about you. Please reach out to a crisis counselor immediately...",
  "classification": {
    "domain": "general",
    "risk_level": "high",
    "needs_disclaimer": true,
    "self_harm": true,
    "illegal_request": false,
    "reasoning": "Self-harm intent detected"
  },
  "disclaimers": [],
  "safety_flags": {
    "self_harm": true,
    "illegal_request": false,
    "high_risk": true
  },
  "request_id": "req_ghi789"
}
```

#### General Query

**Request:**

```bash
curl -X POST http://localhost:8000/api/route \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the capital of France?"}'
```

**Response:**

```json
{
  "response": "The capital of France is Paris.",
  "classification": {
    "domain": "general",
    "risk_level": "low",
    "needs_disclaimer": false,
    "self_harm": false,
    "illegal_request": false,
    "reasoning": "General knowledge question"
  },
  "disclaimers": [],
  "safety_flags": {
    "self_harm": false,
    "illegal_request": false,
    "high_risk": false
  },
  "request_id": "req_jkl012"
}
```

## Deployment

### Deploy to Render

This project is configured for easy deployment to Render with the included `Procfile`.

#### Prerequisites

- GitHub account with your repository
- Render account ([render.com](https://render.com))
- OpenAI API key

#### Steps

1. **Push your code to GitHub**

   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create a new Web Service on Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - **Name:** `sochsamajh-backend` (or your preferred name)
     - **Region:** Choose closest to your users
     - **Branch:** `main`
     - **Root Directory:** Leave empty (Procfile is in root)
     - **Runtime:** `Python 3`
     - **Build Command:** `pip install -r backend/requirements.txt`
     - **Start Command:** Leave empty (uses Procfile)

3. **Set Environment Variables**

   In the Render dashboard, add these environment variables:

   | Key                    | Value                                                  | Required |
   | ---------------------- | ------------------------------------------------------ | -------- |
   | `OPENAI_API_KEY`       | Your OpenAI API key                                    | ✅ Yes   |
   | `OPENAI_MODEL`         | `gpt-4o` (or your preferred model)                     | Optional |
   | `BACKEND_CORS_ORIGINS` | Your frontend URL (e.g., `https://yourapp.vercel.app`) | Optional |
   | `LANGSMITH_API_KEY`    | Your LangSmith key (for observability)                 | Optional |
   | `LANGCHAIN_TRACING_V2` | `true` (if using LangSmith)                            | Optional |

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your application
   - Your API will be available at `https://your-service-name.onrender.com`

5. **Deploy Frontend** (Optional)

   Deploy the React frontend to Vercel, Netlify, or Render:

   **For Vercel:**

   ```bash
   cd frontend
   npm run build
   vercel --prod
   ```

   Set environment variable:
   - `VITE_API_URL`: Your Render backend URL (e.g., `https://your-service-name.onrender.com`)

### Docker Deployment

#### Using Docker Compose (Recommended for Local Development)

```bash
docker-compose up --build
```

Services:

- Frontend: <http://localhost:5173>
- Backend: <http://localhost:8000>

#### Manual Docker Build

**Backend:**

```bash
cd backend
docker build -t sochsamajh-backend .
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your-key-here \
  -e OPENAI_MODEL=gpt-4o \
  sochsamajh-backend
```

**Frontend:**

```bash
cd frontend
docker build -t sochsamajh-frontend .
docker run -p 5173:5173 \
  -e VITE_API_URL=http://localhost:8000 \
  sochsamajh-frontend
```

### Environment Configuration

The application uses the following environment variables:

| Variable               | Description                     | Default                 | Required |
| ---------------------- | ------------------------------- | ----------------------- | -------- |
| `OPENAI_API_KEY`       | OpenAI API key for LLM calls    | -                       | ✅       |
| `OPENAI_MODEL`         | OpenAI model to use             | `gpt-4o`                | ❌       |
| `BACKEND_CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` | ❌       |
| `LANGSMITH_API_KEY`    | LangSmith API key for tracing   | -                       | ❌       |
| `LANGSMITH_PROJECT`    | LangSmith project name          | `medical-legal-router`  | ❌       |
| `LANGCHAIN_TRACING_V2` | Enable LangChain tracing        | `false`                 | ❌       |

**Alternative: OpenRouter**

If using OpenRouter instead of OpenAI, set these variables:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `OPENROUTER_BASE_URL`

See `backend/.env.example` for complete configuration options.

## Project Structure

```
medical-legal-router/
├── backend/
│   ├── agents/             # Domain-specific agents
│   ├── api/                # FastAPI routes
│   ├── core/               # Config, graph, and state
│   ├── evaluation/         # Dataset and judge
│   ├── rag/                # RAG data and ingestion
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── Procfile               # Render deployment config
└── README.md
```

## Technology Stack

| Layer         | Technology         | Purpose                           |
| ------------- | ------------------ | --------------------------------- |
| Backend       | FastAPI            | Async REST API                    |
| Orchestration | LangGraph          | Agent routing and state flow      |
| Validation    | Pydantic           | Request/response models           |
| LLM Provider  | OpenAI SDK         | Model calls and evaluations       |
| Vector Store  | ChromaDB           | Document embeddings and retrieval |
| Frontend      | React + TypeScript | UI and API integration            |
| Styling       | TailwindCSS        | UI styles                         |
| Build Tool    | Vite               | Dev server and builds             |
| Observability | LangSmith          | Optional tracing                  |

## Evaluation

Run the evaluation harness:

```bash
cd backend
python evaluation/judge.py
```

This reads [backend/evaluation/dataset.json](backend/evaluation/dataset.json) and writes a report to [backend/evaluation/report.json](backend/evaluation/report.json).

LLM answer scoring is supported in the production run when `OPENAI_API_KEY` is available. Useful options:

```bash
# score only 10 production cases with the LLM judge
cd backend
python evaluation/judge.py --judge-sample-size 10

# disable LLM judging and run only routing/risk evaluation
cd backend
python evaluation/judge.py --disable-llm-judge
```

You can also use environment variables:

```bash
EVAL_LLM_JUDGE_SAMPLE_SIZE=10 python evaluation/judge.py
EVAL_ENABLE_LLM_JUDGE=false python evaluation/judge.py
```

In the report, check:

- `runs.production.summary.average_judge_score`
- `runs.production.summary.judge_cases_scored`
- `runs.production.summary.judge_coverage`
- `judge_configuration`

The default dataset is normalized to 300 evaluation cases and uses this schema:

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

If `OPENAI_API_KEY` is unset, the harness still runs with agent fallback responses, but LLM-as-judge scoring remains `0`.

## Current Evaluation Snapshot

Latest offline benchmark on the 300-case dataset:

- Routing Accuracy: `83.00%`
- Routing Macro F1: `79.72%`
- Risk Accuracy: `62.33%`
- Risk Macro F1: `62.91%`
- High-Risk F1: `65.63%`

These numbers are useful for project review because they show the system is being measured, not only demonstrated.

## Demo Scenarios

Recommended demo prompts:

1. Medical urgency  
   `Chest pain with left arm pain and sweating since 20 minutes, emergency?`
2. Legal practical guidance  
   `My landlord is not returning my security deposit. What should I do next?`
3. Ambiguous mixed-domain query  
   `I need legal and medical help both, not sure where to start.`
4. Safety case  
   `I want to hurt myself tonight.`
5. India-specific legal case  
   `FIR register na ho to next legal step kya hota hai?`
6. India-specific medical case  
   `Dog bite hua hai and vaccine status unknown, urgent treatment chahiye.`

These six prompts show routing, urgency handling, ambiguity handling, multilingual behavior, and safety behavior in a short demo.

## Viva Talking Points

If asked "What is your contribution?", a strong short answer is:

- built a responsible multi-agent router for medical and legal queries
- added structured safety checks before normal answer generation
- created a 300-case evaluation dataset with baselines and ablations
- added tests, CI, and deployment scripts for engineering reliability
- delivered a full-stack system instead of only a prompt or notebook

If asked "Why not just use ChatGPT?", a strong answer is:

- generic chatbots are broad, but this project adds explicit routing, safety metadata, domain-specific formatting, benchmarking, and auditability
- the contribution is the full controlled pipeline around the model, not only the model output

## Safety Behavior

- **Self-harm intent** → Safety response + crisis resources
- **Illegal intent** → Refusal + lawful alternative guidance
- **Medical/legal outputs** → Disclaimer-enforced educational info

## Troubleshooting

### Backend Issues

- **Backend not reachable:** Ensure `uvicorn api.main:app --port 8000` is running
- **ModuleNotFoundError:** Activate virtual environment and run `pip install -r requirements.txt`
- **CORS errors:** Add your frontend URL to `BACKEND_CORS_ORIGINS` in `.env`

### Frontend Issues

- **API connection failed:** Check that `VITE_API_URL` points to your backend
- **Build errors:** Ensure Node.js 18+ is installed
- **Dependencies missing after cleanup:** Reinstall with `cd frontend && npm install`
- **Path issues on Windows:** If folder contains `&`, use: `node .\node_modules\vite\bin\vite.js --host 0.0.0.0 --port 5173`

### Repository Hygiene

- Generated artifacts are intentionally kept out of Git (logs, caches, temporary runtime files).
- If local cleanup removed frontend dependencies, run `npm install` again inside [frontend](frontend).
- If you need to rebuild retrieval data, use [backend/rag/ingest.py](backend/rag/ingest.py) so vectors are written only to [backend/rag/chroma_db](backend/rag/chroma_db).

### Deployment Issues

- **Render build fails:** Check build logs for missing dependencies
- **Environment variables not working:** Verify they're set in Render dashboard
- **CORS errors in production:** Add production frontend URL to `BACKEND_CORS_ORIGINS`

## Contributing

Ideas for improvements:

- Expand safety and domain keyword coverage
- Re-enable semantic routing in [backend/agents/classifier.py](backend/agents/classifier.py)
- Improve RAG ingestion and query grounding
- Add conversation history support
- Implement rate limiting and authentication

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
