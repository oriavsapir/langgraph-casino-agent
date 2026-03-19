# Casino Property Concierge — AI-Powered Conversational Agent

A production-grade conversational AI agent that answers guest questions about a specific casino property. Built with **LangGraph**, **FastAPI**, and **RAG** (Retrieval-Augmented Generation) over structured property knowledge.

**Loaded property:** Mohegan Sun (Uncasville, CT)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Layer                        │
│   POST /api/v1/chat       GET /api/v1/health               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Agent                          │
│                                                             │
│  START ──► classify ──┬── property_question ──► retrieve    │
│                       │                           │         │
│                       │                        generate     │
│                       │                           │         │
│                       │                          END        │
│                       ├── action_request ──► decline ► END  │
│                       ├── off_topic ──────► decline ► END   │
│                       ├── greeting ──────► greet ──► END    │
│                       └── farewell ──────► farewell ► END   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Knowledge Layer                           │
│  Markdown files ──► Chunking ──► ChromaDB vector store      │
│                                  (semantic similarity)      │
└─────────────────────────────────────────────────────────────┘
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
├── app/
│   ├── main.py                  # FastAPI application entry-point
│   ├── config.py                # Pydantic settings (env-based configuration)
│   ├── api/
│   │   ├── schemas.py           # Request/response Pydantic models
│   │   ├── routes.py            # API endpoint handlers
│   │   └── dependencies.py      # App context factory (wires everything)
│   ├── agent/
│   │   ├── state.py             # LangGraph state definition
│   │   ├── nodes.py             # Graph nodes (classify, retrieve, generate, …)
│   │   └── graph.py             # Graph construction and compilation
│   ├── knowledge/
│   │   ├── loader.py            # Markdown ingestion and chunking
│   │   └── store.py             # ChromaDB vector store wrapper
│   └── data/properties/
│       └── mohegan_sun/         # Property knowledge base (7 markdown files)
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── test_loader.py           # Document loader tests
│   ├── test_store.py            # Vector store tests
│   ├── test_nodes.py            # Individual node tests (mocked LLM)
│   ├── test_graph.py            # Full graph integration tests (mocked LLM)
│   └── test_api.py              # API endpoint tests
├── Dockerfile                   # Multi-stage: runtime + test targets
├── docker-compose.yml           # App + test services
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
# Edit .env: set OPENAI_API_KEY (default) or LLM_PROVIDER=gemini + GEMINI_API_KEY

# Run the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Docker Setup

```bash
# Configure environment
cp .env.example .env
# Edit .env: set OPENAI_API_KEY (default) or LLM_PROVIDER=gemini + GEMINI_API_KEY

# Build and run
docker compose up --build

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

**Response:**
```json
{
  "reply": "We have two excellent Italian dining options! Todd English's Tuscany in Casino of the Sky serves rustic Italian cuisine with an open kitchen and wood-burning oven (Wed–Sun, 5–10 PM, $$$$). Ballo Italian Restaurant in Casino of the Earth offers contemporary Italian dishes (Thu–Mon, 5–10 PM, $$$). Reservations are recommended for both.",
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
# Run all tests
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=term-missing
```

All tests mock the LLM so they run **without an OpenAI API key** and complete in seconds.

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

## Future Improvements

- **Streaming responses** via Server-Sent Events for better UX
- **Persistent checkpointer** (Redis/PostgreSQL) for cross-restart session continuity
- **Hybrid retrieval** combining semantic search with keyword/BM25 scoring
- **Multi-property support** with dynamic property switching
- **Observability** with LangSmith tracing for production debugging
- **Rate limiting** and authentication for production API deployment
- **Response validation node** to detect and retry hallucinated answers
- **Chat UI** — a lightweight frontend for demo purposes
