# AI Automation Pipeline

Business process automation system powered by AI agents and intelligent workflows. Processes hundreds of tasks per hour using Claude API and FastAPI.

## Features

- Multi-agent AI orchestration with Claude API
- REST API built with FastAPI
- Intelligent task routing and prioritization
- Real-time monitoring dashboard
- Webhook integrations for popular business tools
- Retry logic and error handling

## Tech Stack

- **Python 3.11+**
- **Claude API** (Anthropic) — AI agent backbone
- **FastAPI** — High-performance REST API
- **Celery + Redis** — Async task queue
- **PostgreSQL** — Persistent storage
- **Docker** — Containerization

## Getting Started

```bash
# Clone the repo
git clone https://github.com/totem451/ai-automation-pipeline.git
cd ai-automation-pipeline

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Add your ANTHROPIC_API_KEY

# Run the API
uvicorn main:app --reload
```

## Architecture

```
Client → FastAPI → Task Router → Claude Agent → Action Executor → Result Store
                                      ↓
                              Knowledge Base
```

## License

MIT — built by [TL Studio](https://github.com/totem451)
