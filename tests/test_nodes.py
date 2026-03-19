"""Tests for individual LangGraph nodes (LLM calls are mocked)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.nodes import (
    build_classify_node,
    build_generate_node,
    build_retrieve_node,
    build_simple_response_node,
    route_by_intent,
    GREETING_MESSAGE,
    DECLINE_ACTION_MESSAGE,
)
from app.agent.state import AgentState
from app.knowledge.store import PropertyKnowledgeStore


def _make_state(user_text: str = "Hello", **overrides) -> AgentState:
    base: AgentState = {
        "messages": [HumanMessage(content=user_text)],
        "intent": "property_question",
        "retrieved_docs": [],
        "property_name": "Mohegan Sun",
    }
    base.update(overrides)
    return base


class TestClassifyNode:
    @pytest.mark.asyncio
    async def test_parses_intent_from_llm(self, mock_llm: MagicMock):
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(content='{"intent": "greeting"}')
        )
        node = build_classify_node(mock_llm)
        result = await node(_make_state("Hi there"))
        assert result["intent"] == "greeting"

    @pytest.mark.asyncio
    async def test_defaults_to_property_question_on_bad_json(self, mock_llm: MagicMock):
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(content="not valid json")
        )
        node = build_classify_node(mock_llm)
        result = await node(_make_state("whatever"))
        assert result["intent"] == "property_question"

    @pytest.mark.asyncio
    async def test_action_request_detected(self, mock_llm: MagicMock):
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(content='{"intent": "action_request"}')
        )
        node = build_classify_node(mock_llm)
        result = await node(_make_state("Book me a room"))
        assert result["intent"] == "action_request"


class TestRetrieveNode:
    @pytest.mark.asyncio
    async def test_retrieves_documents(self, knowledge_store: PropertyKnowledgeStore):
        node = build_retrieve_node(knowledge_store, k=2)
        state = _make_state("What restaurants do you have?")
        result = await node(state)
        assert "retrieved_docs" in result
        assert len(result["retrieved_docs"]) > 0

    @pytest.mark.asyncio
    async def test_respects_k(self, knowledge_store: PropertyKnowledgeStore):
        node = build_retrieve_node(knowledge_store, k=1)
        result = await node(_make_state("Tell me about poker"))
        assert len(result["retrieved_docs"]) <= 1


class TestGenerateNode:
    @pytest.mark.asyncio
    async def test_generates_ai_message(self, mock_llm: MagicMock):
        mock_llm.ainvoke = AsyncMock(
            return_value=AIMessage(content="We have several fine dining options.")
        )
        node = build_generate_node(mock_llm)
        state = _make_state(
            "What restaurants do you have?",
            retrieved_docs=[
                Document(
                    page_content="Todd English's Tuscany serves Italian cuisine.",
                    metadata={},
                )
            ],
        )
        result = await node(state)
        assert len(result["messages"]) == 1
        assert "fine dining" in result["messages"][0].content.lower()


class TestSimpleResponseNode:
    @pytest.mark.asyncio
    async def test_greeting_node(self):
        node = build_simple_response_node(GREETING_MESSAGE)
        result = await node(_make_state("Hi"))
        reply = result["messages"][0].content
        assert "Mohegan Sun" in reply

    @pytest.mark.asyncio
    async def test_decline_action_node(self):
        node = build_simple_response_node(DECLINE_ACTION_MESSAGE)
        result = await node(_make_state("Book a room"))
        reply = result["messages"][0].content
        assert "reservation" in reply.lower() or "booking" in reply.lower()


class TestRouteByIntent:
    @pytest.mark.parametrize(
        "intent, expected_route",
        [
            ("property_question", "retrieve"),
            ("action_request", "decline_action"),
            ("off_topic", "decline_off_topic"),
            ("greeting", "greet"),
            ("farewell", "farewell"),
        ],
    )
    def test_routes_correctly(self, intent: str, expected_route: str):
        state = _make_state(intent=intent)
        assert route_by_intent(state) == expected_route

    def test_unknown_intent_defaults_to_retrieve(self):
        state = _make_state(intent="some_unknown_thing")
        assert route_by_intent(state) == "retrieve"
