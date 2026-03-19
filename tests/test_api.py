"""Tests for the FastAPI endpoints (agent is mocked end-to-end)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage

from app.api.routes import init_routes, router
from app.api.schemas import ChatResponse


def _build_test_app() -> FastAPI:
    """Build a minimal FastAPI app (no lifespan) for unit testing."""
    test_app = FastAPI()
    test_app.include_router(router, prefix="/api/v1")
    return test_app


@pytest.fixture()
def client():
    """Create a test client with mocked dependencies so no LLM key is needed."""
    mock_agent = MagicMock()
    mock_agent.ainvoke = AsyncMock(
        return_value={
            "messages": [
                HumanMessage(content="Hello"),
                AIMessage(content="Welcome to Mohegan Sun!"),
            ],
        }
    )

    mock_store = MagicMock()
    mock_store.document_count = 42

    mock_ctx = MagicMock()
    mock_ctx.agent = mock_agent
    mock_ctx.store = mock_store
    mock_ctx.property_display_name = "Mohegan Sun"

    from app.api import routes
    routes._ctx = mock_ctx

    app = _build_test_app()
    with TestClient(app) as c:
        yield c

    routes._ctx = None


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["property"] == "Mohegan Sun"
        assert data["documents_loaded"] == 42


class TestChatEndpoint:
    def test_chat_returns_reply(self, client: TestClient):
        resp = client.post(
            "/api/v1/chat",
            json={"message": "What restaurants do you have?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert "session_id" in data
        assert data["property_name"] == "Mohegan Sun"

    def test_chat_with_session_id(self, client: TestClient):
        resp = client.post(
            "/api/v1/chat",
            json={"message": "Hello", "session_id": "my-session-123"},
        )
        assert resp.status_code == 200
        assert resp.json()["session_id"] == "my-session-123"

    def test_chat_empty_message_rejected(self, client: TestClient):
        resp = client.post("/api/v1/chat", json={"message": ""})
        assert resp.status_code == 422

    def test_chat_missing_message_rejected(self, client: TestClient):
        resp = client.post("/api/v1/chat", json={})
        assert resp.status_code == 422

    def test_chat_long_message_rejected(self, client: TestClient):
        resp = client.post("/api/v1/chat", json={"message": "x" * 2001})
        assert resp.status_code == 422

    def test_chat_agent_error_returns_502(self, client: TestClient):
        from app.api import routes
        routes._ctx.agent.ainvoke = AsyncMock(side_effect=RuntimeError("LLM down"))
        resp = client.post("/api/v1/chat", json={"message": "Hello"})
        assert resp.status_code == 502
