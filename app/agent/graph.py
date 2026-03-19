"""Builds and compiles the LangGraph conversational agent.

Graph topology
--------------

    START
      │
      ▼
  ┌─────────┐
  │ classify │  ← LLM-based intent classification
  └────┬─────┘
       │ (conditional routing)
       ├── property_question ──► retrieve ──► generate ──► END
       ├── action_request   ──► decline_action ──────────► END
       ├── off_topic        ──► decline_off_topic ───────► END
       ├── greeting         ──► greet ───────────────────► END
       └── farewell         ──► farewell ────────────────► END
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    DECLINE_ACTION_MESSAGE,
    DECLINE_OFF_TOPIC_MESSAGE,
    FAREWELL_MESSAGE,
    GREETING_MESSAGE,
    build_classify_node,
    build_generate_node,
    build_retrieve_node,
    build_simple_response_node,
    route_by_intent,
)
from app.agent.state import AgentState
from app.knowledge.store import PropertyKnowledgeStore


def build_graph(
    llm: BaseChatModel,
    store: PropertyKnowledgeStore,
    retrieval_k: int = 6,
) -> StateGraph:
    """Construct the state graph (uncompiled) for the property concierge agent."""

    graph = StateGraph(AgentState)

    graph.add_node("classify", build_classify_node(llm))
    graph.add_node("retrieve", build_retrieve_node(store, k=retrieval_k))
    graph.add_node("generate", build_generate_node(llm))
    graph.add_node("decline_action", build_simple_response_node(DECLINE_ACTION_MESSAGE))
    graph.add_node("decline_off_topic", build_simple_response_node(DECLINE_OFF_TOPIC_MESSAGE))
    graph.add_node("greet", build_simple_response_node(GREETING_MESSAGE))
    graph.add_node("farewell", build_simple_response_node(FAREWELL_MESSAGE))

    graph.add_edge(START, "classify")

    graph.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "retrieve": "retrieve",
            "decline_action": "decline_action",
            "decline_off_topic": "decline_off_topic",
            "greet": "greet",
            "farewell": "farewell",
        },
    )

    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    graph.add_edge("decline_action", END)
    graph.add_edge("decline_off_topic", END)
    graph.add_edge("greet", END)
    graph.add_edge("farewell", END)

    return graph


def compile_graph(
    llm: BaseChatModel,
    store: PropertyKnowledgeStore,
    retrieval_k: int = 6,
):
    """Build, compile with an in-memory checkpointer, and return the runnable."""
    graph = build_graph(llm, store, retrieval_k)
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)
