# Enterprise Agentic Automation (UPM FYP)

This workspace is prepared for a Final Year Project (FYP) on building a multi-agent automation system.

## Project Goal

Build a web-based Multi-Agent System (MAS) that can accept one natural-language business request and automatically coordinate at least three agents:

- Marketing Agent
- Schedule Agent
- Document Agent

The system is orchestrated by an Orchestrator Agent (Openclaw or LangChain-style architecture).

## Software Stack (Implemented)

- Language: Python 3.10+
- Backend: FastAPI
- Frontend: HTML + CSS + Vanilla JavaScript
- Architecture: Orchestrator + 3 Specialized Agents
- Storage: SQLite (evaluation logs)

## What Is Included

- `app/`: runnable software prototype (web + orchestrator + agents).
- `requirements.txt`: Python dependencies.

## Run the Software

- Quick start (recommended on Windows): double-click `run_local_free.bat` (configures local Ollama mode and starts the app).

1. Create virtual env (optional but recommended):
   - Windows PowerShell: `python -m venv .venv`
   - Activate: `.venv\Scripts\Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start app:
   - `uvicorn app.main:app --reload`
4. Open browser:
   - [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Evaluation Features

- Every workflow run is saved into local SQLite database: `app_data.db`
- Metrics summary API: `GET /api/metrics/summary`
- HITL queue API: `GET /api/hitl/pending`
- HITL review API: `POST /api/hitl/review`
- CSV export API: `GET /api/metrics/export.csv`
- Batch experiment API: `POST /api/experiments/run`
- Preset list API: `GET /api/experiments/presets`
- Run preset API: `POST /api/experiments/run-preset`
- Auto report API: `POST /api/reports/generate`
- Built-in web dashboard supports:
  - Run workflow
  - Refresh metrics
  - Download CSV for thesis analysis
  - Run multiple prompts in one batch experiment
  - One-click A/B/C preset experiment scenarios
  - One-click generate experiment report for thesis chapter

## Optional Real LLM Setup (OpenAI)

If you want real model outputs instead of mock generation, set these environment variables before running:

- `OPENAI_API_KEY`
- `ROUTER_MODEL` (optional, default: `gpt-4.1-nano`)
- `GENERATOR_MODEL` (optional, default: `gpt-4.1-mini`)

PowerShell example:

`$env:OPENAI_API_KEY="your_key_here"`
`$env:ROUTER_MODEL="gpt-4.1-nano"`
`$env:GENERATOR_MODEL="gpt-4.1-mini"`
`python -m uvicorn app.main:app --reload`

## Free Local LLM Setup (Recommended)

This project supports a fully local and free LLM mode with Ollama.

1. Install Ollama: [https://ollama.com/download](https://ollama.com/download)
2. Pull a model in PowerShell:
   - `ollama pull qwen2.5:7b-instruct`
3. Set environment variables before starting app:
   - `$env:LLM_PROVIDER="local"`
   - `$env:OLLAMA_MODEL="qwen2.5:7b-instruct"`
   - `$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"` (optional)
4. Start app:
   - `python -m uvicorn app.main:app --reload`

If local Ollama is unavailable, the system safely falls back to mock text generation.

## Schedule Tool Provider Switch

- Default mode is mock scheduler.
- To show "real integration architecture" in demo:
  - Set env var `SCHEDULE_PROVIDER=google`
  - System will route schedule calls to the Google integration placeholder in `app/services/schedule_tool.py`
  - You can implement real OAuth/API calls in that method later without changing the agent/orchestrator flow

## Core Deliverables (Aligned with Lecturer Expectations)

1. Core system prototype (3+ connected agents in one workflow).
2. Agentic framework implementation with custom tool bindings.
3. Academic thesis with performance, latency, cost, and success-rate analysis.

## Suggested Next Steps

1. Run the web UI and test a multi-agent business request end-to-end.
2. Finalize tool integrations (calendar, social platform, document export).
3. Collect workflow metrics from `app_data.db` for thesis evaluation.

