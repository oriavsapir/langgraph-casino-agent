"""Tests for the compiled LangGraph agent (LLM is mocked)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agent.graph import build_graph, compile_graph
from app.knowledge.store import PropertyKnowledgeStore


def _mock_llm_factory(intent: str = "property_question", response: str = "Mocked response"):
    """Create a mock LLM that returns *intent* on the first call (classify)
    and *response* on the second call (generate)."""
    llm = MagicMock()
    call_count = {"n": 0}

    async def side_effect(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return AIMessage(content=f'{{"intent": "{intent}"}}')
        return AIMessage(content=response)

    llm.ainvoke = AsyncMock(side_effect=side_effect)
    return llm


class TestBuildGraph:
    def test_graph_has_expected_nodes(self, knowledge_store: PropertyKnowledgeStore):
        llm = MagicMock()
        graph = build_graph(llm, knowledge_store)
        node_names = set(graph.nodes.keys())
        expected = {"classify", "retrieve", "generate", "decline_action", "decline_off_topic", "greet", "farewell"}
        assert expected == node_names


class TestCompiledGraph:
    @pytest.mark.asyncio
    async def test_property_question_flow(self, knowledge_store: PropertyKnowledgeStore):
        llm = _mock_llm_factory("property_question", "We have great Italian dining at Tuscany!")
        agent = compile_graph(llm, knowledge_store)
        result = await agent.ainvoke(
            {
                "messages": [HumanMessage(content="What restaurants do you have?")],
                "property_name": "Mohegan Sun",
                "intent": "property_question",
                "retrieved_docs": [],
            },
            config={"configurable": {"thread_id": "test-1"}},
        )
        ai_msgs = [m for m in result["messages"] if m.type == "ai"]
        assert len(ai_msgs) >= 1
        assert len(ai_msgs[-1].content) > 0

    @pytest.mark.asyncio
    async def test_greeting_flow(self, knowledge_store: PropertyKnowledgeStore):
        llm = _mock_llm_factory("greeting")
        agent = compile_graph(llm, knowledge_store)
        result = await agent.ainvoke(
            {
                "messages": [HumanMessage(content="Hello!")],
                "property_name": "Mohegan Sun",
                "intent": "property_question",
                "retrieved_docs": [],
            },
            config={"configurable": {"thread_id": "test-2"}},
        )
        ai_msgs = [m for m in result["messages"] if m.type == "ai"]
        assert "Mohegan Sun" in ai_msgs[-1].content

    @pytest.mark.asyncio
    async def test_action_request_declined(self, knowledge_store: PropertyKnowledgeStore):
        llm = _mock_llm_factory("action_request")
        agent = compile_graph(llm, knowledge_store)
        result = await agent.ainvoke(
            {
                "messages": [HumanMessage(content="Book me a room for Friday")],
                "property_name": "Mohegan Sun",
                "intent": "property_question",
                "retrieved_docs": [],
            },
            config={"configurable": {"thread_id": "test-3"}},
        )
        ai_msgs = [m for m in result["messages"] if m.type == "ai"]
        reply = ai_msgs[-1].content.lower()
        assert "reservation" in reply or "booking" in reply or "not able" in reply

    @pytest.mark.asyncio
    async def test_off_topic_declined(self, knowledge_store: PropertyKnowledgeStore):
        llm = _mock_llm_factory("off_topic")
        agent = compile_graph(llm, knowledge_store)
        result = await agent.ainvoke(
            {
                "messages": [HumanMessage(content="What is the capital of France?")],
                "property_name": "Mohegan Sun",
                "intent": "property_question",
                "retrieved_docs": [],
            },
            config={"configurable": {"thread_id": "test-4"}},
        )
        ai_msgs = [m for m in result["messages"] if m.type == "ai"]
        reply = ai_msgs[-1].content.lower()
        assert "mohegan sun" in reply or "resort" in reply

    @pytest.mark.asyncio
    async def test_conversation_continuity(self, knowledge_store: PropertyKnowledgeStore):
        """Two messages in the same session should share conversation history."""
        llm = MagicMock()
        call_count = {"n": 0}

        async def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] % 2 == 1:
                return AIMessage(content='{"intent": "property_question"}')
            return AIMessage(content=f"Response #{call_count['n'] // 2}")

        llm.ainvoke = AsyncMock(side_effect=side_effect)
        agent = compile_graph(llm, knowledge_store)
        thread = "test-continuity"
        config = {"configurable": {"thread_id": thread}}

        r1 = await agent.ainvoke(
            {
                "messages": [HumanMessage(content="Tell me about dining")],
                "property_name": "Mohegan Sun",
                "intent": "property_question",
                "retrieved_docs": [],
            },
            config=config,
        )
        r2 = await agent.ainvoke(
            {
                "messages": [HumanMessage(content="And the spa?")],
                "property_name": "Mohegan Sun",
                "intent": "property_question",
                "retrieved_docs": [],
            },
            config=config,
        )
        assert len(r2["messages"]) > len(r1["messages"])
