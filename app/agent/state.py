from typing import Annotated, Literal

from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

Intent = Literal[
    "property_question",
    "action_request",
    "off_topic",
    "greeting",
    "farewell",
]


class AgentState(TypedDict):
    """Shared state that flows through every node in the graph."""

    messages: Annotated[list[BaseMessage], add_messages]
    intent: Intent
    retrieved_docs: list[Document]
    property_name: str
