# SochSamajh AI - Responsible Multi-Agent Query Router

Safety-first multi-agent assistant that routes user questions to medical, legal, general, or safety handling.

## Live Demo

- Frontend: <https://mental-legal-router-ii96dikha-sanjeev2004s-projects.vercel.app/>

## What It Does

- Pre-screens for self-harm and illegal intent before normal processing.
- Classifies query domain and risk.
- Routes to domain-specific agent (`medical`, `legal`, `general`, or `safety`).
- Adds appropriate disclaimers.
- Falls back to local canned knowledge if model/API fails.

## Tech Stack

- Backend: FastAPI, LangGraph, Pydantic, LangSmith (optional), OpenAI SDK
- Model Provider: OpenRouter
- Frontend: React, TypeScript, Vite, TailwindCSS

## Architecture Flow

1. `pre_screen`: detect self-harm / illegal intent
2. `classifier`: domain + risk
3. `router`: choose `medical` / `legal` / `general` / `safety`
4. `agent`: generate response
5. `formatter`: clean response + disclaimers

## Project Structure

```text
medical-legal-router/
  backend/
    agents/
      classifier.py
      medical.py
      legal.py
      general.py
      safety.py
      formatter.py
    api/main.py
    core/
      config.py
      graph.py
      state.py
    evaluation/
      test_cases.json
      run_eval.py
    requirements.txt
    .env.example
  frontend/
    src/
    package.json
  docker-compose.yml
```

## Backend Setup

```bash
cd backend
python -m venv .venv
\.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

If you are using Command Prompt instead of PowerShell, run:

```bash
.\.venv\Scripts\activate.bat
copy .env.example .env
```

Set `backend/.env`:

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=openai/gpt-oss-20b:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_SITE_URL=
OPENROUTER_APP_NAME=medical-legal-router
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=medical-legal-router
BACKEND_CORS_ORIGINS=http://localhost:5173
```

Run backend:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

- `http://localhost:8000/api/health`

## Frontend Setup

```bash
cd frontend
npm install
```

Run frontend:

- Normal command:

```bash
npm run dev -- --host 0.0.0.0 --port 5173
```

- If your folder path contains `&` on Windows (like `Medical&LegalROUTER`), use:

```bash
node .\node_modules\vite\bin\vite.js --host 0.0.0.0 --port 5173
```

App URL:

- `http://localhost:5173`

## API

### `GET /api/health`

Returns service status and active model.

### `POST /api/route`

Request:

```json
{
  "query": "What are symptoms of diabetes?"
}
```

Response (shape):

```json
{
  "response": "...",
  "classification": {
    "domain": "medical",
    "risk_level": "low",
    "needs_disclaimer": true,
    "self_harm": false,
    "illegal_request": false,
    "reasoning": "..."
  },
  "disclaimers": ["..."],
  "safety_flags": {
    "self_harm": false,
    "illegal_request": false,
    "high_risk": false
  },
  "request_id": "..."
}
```

## Evaluation

```bash
cd backend
python -m evaluation.run_eval
```

## Docker

```bash
docker-compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## Safety Behavior

- Self-harm intent -> safety response + crisis resources
- Illegal intent -> refusal + lawful alternative guidance
- Medical/legal outputs -> disclaimer-enforced educational info

## Notes

- Responses are cleaned in `backend/agents/formatter.py` to reduce markdown/table clutter.
- If OpenRouter fails, fallback responses are used.

## License

MIT (`LICENSE`)
