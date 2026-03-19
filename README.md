**In a real-world scenario, with the company’s approval, I would likely build a tool that performs scraping of the client website endpoints. I would run a script that collects the site’s endpoints once a day using a cron job to keep the data up to date, and gathers all relevant information.**   
**The collected data would then be stored in a vector database.**   
**Since scraping a website without permission can lead to blocking and legal issues, I instead included the information as Markdown files.**


# Casino Property Concierge — AI-Powered Conversational Agent

A production-grade conversational AI agent that answers guest questions about a specific casino property. Built with **LangGraph**, **FastAPI**, **React**, and **RAG** (Retrieval-Augmented Generation) over structured property knowledge.

**Loaded property:** Mohegan Sun (Uncasville, CT)

---

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           nginx (port 80)               │
                    │  /api/* → app:8000   /* → ui:3000       │
                    └──────────────────┬──────────────────────┘
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         │                             │                             │
         ▼                             ▼                             ▼
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   React UI      │         │  FastAPI API    │         │  LangGraph      │
│   (port 3000)   │         │  (port 8000)    │         │  Agent          │
│   Chat          │         │  /chat  /health │         │  classify →     │
│                 │         │                 │         │  retrieve →     │
└─────────────────┘         └────────┬────────┘         │  generate       │
                                     │                  └────────┬────────┘
                                     │                           │
                                     └───────────────────────────┘
                                                     │
                                                     ▼
                                     ┌─────────────────────────────┐
                                     │  ChromaDB vector store      │
                                     │  (Markdown → chunks)        │
                                     └─────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| **Graph framework** | LangGraph | Required by spec; provides explicit state management, conditional routing, and built-in memory |
| **LLM** | OpenAI or Google Gemini | Configurable via `LLM_PROVIDER` (openai/gemini); OpenAI GPT-4o-mini or Gemini 1.5 Flash by default |
| **Embeddings** | ChromaDB default (all-MiniLM-L6-v2) | Zero-config, runs locally, no API key needed for embeddings |
| **Vector store** | ChromaDB (in-process) | No external infrastructure needed; production-ready upgrade path to client-server mode |
| **Knowledge format** | Markdown files | Human-readable, easy to edit/extend, excellent chunking with header-based splitting |
| **Intent routing** | LLM-based classification | More accurate than keyword matching; handles nuance and context |
| **Guardrails** | Intent classification + system prompt constraints | Two layers of defense: structural (routing) and behavioral (prompt) |
| **API** | FastAPI | Async-native, automatic OpenAPI docs, Pydantic validation |
| **Session management** | LangGraph MemorySaver checkpointer | Built-in conversation memory per session thread |

---

## Project Structure

```
ai-backend/
├── app/                         # Backend API
│   ├── main.py                  # FastAPI application entry-point
│   ├── config.py                # Pydantic settings (LLM provider, keys)
│   ├── api/
│   │   ├── schemas.py           # Request/response Pydantic models
│   │   ├── routes.py            # API endpoint handlers
│   │   └── dependencies.py      # App context (OpenAI or Gemini LLM)
│   ├── agent/
│   │   ├── state.py             # LangGraph state definition
│   │   ├── nodes.py             # Graph nodes (classify, retrieve, generate, …)
│   │   └── graph.py             # Graph construction and compilation
│   ├── knowledge/
│   │   ├── loader.py            # Markdown ingestion and chunking
│   │   └── store.py             # ChromaDB vector store wrapper
│   └── data/properties/
│       └── mohegan_sun/         # Property knowledge base (8 markdown files)
├── ui/                          # React chat frontend
│   ├── src/
│   │   ├── App.tsx              # Main chat layout
│   │   ├── api.ts               # Chat API client
│   │   └── components/          # Header, MessageBubble, InputBar, WelcomeScreen
│   ├── Dockerfile               # Build + serve (port 3000)
│   └── package.json
├── tests/
│   ├── conftest.py              # Shared fixtures (incl. fake ChromaDB embedding)
│   ├── test_loader.py           # Document loader tests
│   ├── test_store.py            # Vector store tests
│   ├── test_nodes.py            # Individual node tests (mocked LLM)
│   ├── test_graph.py            # Full graph integration tests (mocked LLM)
│   └── test_api.py              # API endpoint tests
├── Dockerfile                   # Backend: runtime + test targets
├── docker-compose.yml           # app, ui, nginx, tests
├── nginx.conf                   # Reverse proxy: /api → app, / → ui
├── requirements.txt
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- An **OpenAI API key** or **Google Gemini API key**

### Local Setup

```bash
# Clone and enter the project
cd ai-backend

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — see LLM configuration below

# Run the server
uvicorn app.main:app --reload
```

### LLM Configuration

| Provider | .env settings |
|----------|---------------|
| **OpenAI** (default) | `LLM_PROVIDER=openai`, `OPENAI_API_KEY=sk-...` |
| **Google Gemini** | `LLM_PROVIDER=gemini`, `GEMINI_API_KEY=...` |

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Docker Setup (recommended)

```bash
# Configure environment
cp .env.example .env
# Edit .env — set LLM provider and API key (see LLM Configuration above)

# Build and run (backend + UI + nginx)
docker compose up --build
```

| URL | Service |
|-----|---------|
| **http://localhost** | Chat UI (via nginx) |
| **http://localhost:3000** | React UI directly |
| **http://localhost:8000** | API + Swagger docs |
| **http://localhost:8000/docs** | Interactive API documentation |

```bash
# Run tests in Docker
docker compose run --rm tests
```

---

## API Reference

### `POST /api/v1/chat`

Send a message and receive the agent's response.

**Request:**
```json
{
  "message": "What Italian restaurants do you have?",
  "session_id": "optional-session-id"
}
```

**Response:** (`reply` may contain Markdown — lists, **bold**, etc.)
```json
{
  "reply": "We have two excellent Italian dining options! **Todd English's Tuscany** in Casino of the Sky...",
  "session_id": "a1b2c3d4-...",
  "property_name": "Mohegan Sun"
}
```

### `GET /api/v1/health`

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "property": "Mohegan Sun",
  "documents_loaded": 87
}
```

---

## Running Tests

```bash
# Local: run all tests
pytest

# Local: verbose output
pytest -v

# Local: with coverage
pytest --cov=app --cov-report=term-missing

# Docker: run tests
docker compose run --rm tests
```

- **LLM**: All tests mock the LLM — no OpenAI/Gemini API key required
- **ChromaDB**: Tests use a fake embedding function — no model download; tests complete in seconds

---

## Adding a New Property

1. Create a new directory under `app/data/properties/` (e.g., `twin_arrows/`)
2. Add markdown files covering the property's key areas (overview, dining, entertainment, hotel, gaming, amenities, promotions, practical info)
3. Set `PROPERTY_ID=twin_arrows` in your `.env` file
4. Restart the server — the agent will load the new property automatically

---

## Guardrails & Safety

The agent enforces boundaries through two complementary mechanisms:

1. **Structural guardrails (graph routing):** An LLM-based intent classifier routes messages _before_ the response generation node. Action requests and off-topic questions are routed to dedicated decline nodes that never reach the retrieval/generation pipeline.

2. **Behavioral guardrails (system prompt):** The generation node's system prompt explicitly instructs the LLM to answer only from provided context, never fabricate information, and never discuss other properties.

### What the agent handles:
- Property questions (dining, rooms, gaming, entertainment, spa, promotions, etc.)
- Greetings and farewells
- Polite declines for off-topic questions
- Polite declines for action requests (bookings, reservations, account operations)

---

## UI Features

- **React + TypeScript** — Chat interface with luxury casino styling (dark theme, gold accents)
- **Markdown rendering** — Bot responses support **bold**, lists, headings
- **Session continuity** — Pass `session_id` to maintain conversation context
- **Quick suggestions** — Welcome screen with suggested questions (dining, rooms, gaming, etc.)
- **Responsive layout** — Works on desktop and mobile

# POC
<img width="792" height="927" alt="image" src="https://github.com/user-attachments/assets/3788d2f4-45b7-4a5c-9f69-28692b765426" />
![Uploading image.png…]()

