# SochSamajh AI - Medical and Legal Query Router

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688)

A safety-first multi-agent system that routes medical, legal, and general queries to specialized agents with risk-aware handling and domain-specific disclaimers.

## Key Features

- Pre-screening for self-harm and illegal intent before model calls
- Intent classification across domain and risk level
- Dedicated agents for medical, legal, general, and safety responses
- LangGraph-based routing with critic and formatter stages
- FastAPI backend and React + TypeScript frontend

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

Run the evaluation harness (requires `OPENAI_API_KEY`):

```bash
cd backend
python evaluation/judge.py
```

This reads [backend/evaluation/dataset.json](backend/evaluation/dataset.json) and writes a report to [backend/evaluation/report.json](backend/evaluation/report.json).

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
- **Path issues on Windows:** If folder contains `&`, use: `node .\node_modules\vite\bin\vite.js --host 0.0.0.0 --port 5173`

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
