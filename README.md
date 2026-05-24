# AI Automation Pipeline

An AI-powered task automation pipeline built with **FastAPI** and **Google Gemini**. Post a natural-language instruction via REST API; an autonomous ReAct agent executes it by reasoning step-by-step and calling tools (calculator, web search, date/time) until it produces a final answer.

## What it demonstrates

- **ReAct agent pattern** (Reason → Act → Observe → repeat) implemented from scratch
- **Gemini function calling** to let the model decide which tools to invoke
- **Async background tasks** via FastAPI's `BackgroundTasks`
- **Clean layered architecture**: API → Services → Storage
- **Pydantic v2** models with full validation
- Docker + docker-compose for zero-friction deployment

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          CLIENT                             │
│              POST /api/v1/tasks  {"instruction": "..."}     │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼──────────────────────────────────┐
│                       FastAPI App                           │
│                                                             │
│  ┌─────────────────┐   ┌────────────────────────────────┐  │
│  │  /health        │   │  /api/v1/tasks  (CRUD routes)  │  │
│  └─────────────────┘   └───────────────┬────────────────┘  │
│                                        │ BackgroundTask     │
│                         ┌──────────────▼──────────────┐    │
│                         │      ReAct Agent Loop        │    │
│                         │  ┌────────────────────────┐  │    │
│                         │  │  1. Send to Gemini      │  │    │
│                         │  │  2. function_call?       │  │    │
│                         │  │     yes → run tool       │  │    │
│                         │  │     no  → final answer   │  │    │
│                         │  └────────────────────────┘  │    │
│                         └──────────────┬────────────────┘   │
│                                        │                     │
│              ┌─────────────────────────┼──────────────────┐ │
│              │         Tools           │                  │ │
│              │  ┌──────────┐  ┌────────┴────┐  ┌────────┐│ │
│              │  │calculator│  │ web_search  │  │datetime││ │
│              │  └──────────┘  └─────────────┘  └────────┘│ │
│              └───────────────────────────────────────────┘  │
│                                                             │
│                  In-Memory TaskStore (asyncio.Lock)         │
└─────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

| Method | Path                      | Status | Description                                       |
|--------|---------------------------|--------|---------------------------------------------------|
| GET    | `/health`                 | 200    | Service health check                              |
| POST   | `/api/v1/tasks`           | 202    | Create & enqueue a task (returns immediately)     |
| GET    | `/api/v1/tasks`           | 200    | List all tasks                                    |
| GET    | `/api/v1/tasks/{task_id}` | 200    | Get a specific task by ID                         |

Interactive docs available at `http://localhost:8000/docs`

---

## Quick Start

### Local (without Docker)

**Prerequisites:** Python 3.11+, a [Google Gemini API key](https://aistudio.google.com/app/apikey)

```bash
# 1. Clone
git clone https://github.com/totem451/ai-automation-pipeline.git
cd ai-automation-pipeline

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY

# 5. Run
uvicorn main:app --reload
```

The API is now available at `http://localhost:8000`.

### Docker

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY

# 2. Build and start
docker-compose up --build
```

---

## Example Usage

### Create a task

```bash
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"instruction": "What is 1337 * 42? Also tell me what day of the week it is today."}'
```

**Response (202 Accepted):**
```json
{
  "id": "a3f1c2d4-8b5e-4f3a-9c1d-2e7f6a8b3c4d",
  "instruction": "What is 1337 * 42? Also tell me what day of the week it is today.",
  "status": "pending",
  "steps": [],
  "result": null,
  "error": null,
  "created_at": "2024-11-15T10:30:00.000Z",
  "updated_at": "2024-11-15T10:30:00.000Z"
}
```

### Poll for the result

```bash
curl http://localhost:8000/api/v1/tasks/a3f1c2d4-8b5e-4f3a-9c1d-2e7f6a8b3c4d
```

**Response (once completed):**
```json
{
  "id": "a3f1c2d4-8b5e-4f3a-9c1d-2e7f6a8b3c4d",
  "instruction": "What is 1337 * 42? Also tell me what day of the week it is today.",
  "status": "completed",
  "steps": [
    {
      "thought": "Iteration 1: Calling tool 'calculate'",
      "action": "calculate",
      "action_input": {"expression": "1337 * 42"},
      "observation": "56154"
    },
    {
      "thought": "Iteration 2: Calling tool 'get_current_datetime'",
      "action": "get_current_datetime",
      "action_input": {},
      "observation": "Current date and time (UTC): Friday, 2024-11-15 10:30:05 UTC"
    },
    {
      "thought": "Iteration 3: Final answer produced.",
      "action": null,
      "action_input": null,
      "observation": "1337 × 42 = **56,154**. Today is Friday, November 15, 2024."
    }
  ],
  "result": "1337 × 42 = **56,154**. Today is Friday, November 15, 2024.",
  "error": null,
  "created_at": "2024-11-15T10:30:00.000Z",
  "updated_at": "2024-11-15T10:30:08.000Z"
}
```

### List all tasks

```bash
curl http://localhost:8000/api/v1/tasks
```

### More task examples

```bash
# Web search
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Search the web for the latest Python 3.13 release highlights."}'

# Pure math
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Calculate (2**32) / 1024 / 1024 and tell me what that number represents."}'

# Multi-step research + calculation
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Find the population of Tokyo and calculate how many times larger it is than a city of 500,000 people."}'
```

---

## Available Tools

| Tool                   | Description                                                  |
|------------------------|--------------------------------------------------------------|
| `calculate`            | Safe math evaluation via Python AST — no `eval` involved     |
| `get_current_datetime` | Returns the current UTC date and time                        |
| `web_search`           | DuckDuckGo search, returns top-N results with titles & URLs  |

---

## Project Structure

```
ai-automation-pipeline/
├── main.py                          # FastAPI app entry point
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── app/
    ├── core/
    │   └── config.py                # pydantic-settings configuration
    ├── models/
    │   └── task.py                  # Task, TaskCreate, TaskStep, TaskStatus
    ├── api/
    │   └── routes/
    │       ├── tasks.py             # POST/GET /tasks endpoints
    │       └── health.py            # GET /health
    ├── services/
    │   ├── gemini_client.py         # Async Gemini API wrapper
    │   ├── agent.py                 # ReAct agent loop
    │   └── tools/
    │       ├── registry.py          # Tool registry + FunctionDeclarations
    │       ├── calculator.py        # AST-based safe math evaluator
    │       ├── datetime_tool.py     # Current date/time utility
    │       └── web_search.py        # DuckDuckGo search wrapper
    └── storage/
        └── task_store.py            # Async in-memory task store
```

---

## Environment Variables

| Variable               | Required | Default              | Description                         |
|------------------------|----------|----------------------|-------------------------------------|
| `GEMINI_API_KEY`       | Yes      | —                    | Google Gemini API key               |
| `GEMINI_MODEL`         | No       | `gemini-2.0-flash`   | Gemini model identifier             |
| `MAX_AGENT_ITERATIONS` | No       | `10`                 | Max ReAct loop iterations per task  |

---

## License

MIT — built by [TL Studio](https://github.com/totem451)
