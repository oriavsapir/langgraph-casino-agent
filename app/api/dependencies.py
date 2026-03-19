"""Application-wide singletons created once at startup."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app.agent.graph import compile_graph
from app.config import Settings
from app.knowledge.loader import load_property_documents
from app.knowledge.store import PropertyKnowledgeStore

logger = logging.getLogger(__name__)


def _create_llm(settings: Settings) -> BaseChatModel:
    """Create the LLM instance based on configured provider."""
    provider = settings.llm_provider.lower()
    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=settings.gemini_api_key,
            temperature=0.3,
        )
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
    )


@dataclass
class AppContext:
    """Holds the compiled LangGraph agent and related resources."""

    settings: Settings
    store: PropertyKnowledgeStore
    agent: Any = field(init=False)
    property_display_name: str = field(init=False)

    def __post_init__(self) -> None:
        llm = _create_llm(self.settings)
        self.agent = compile_graph(
            llm=llm,
            store=self.store,
            retrieval_k=self.settings.retrieval_k,
        )
        self.property_display_name = (
            self.settings.property_id.replace("_", " ").title()
        )
        logger.info(
            "AppContext ready — property=%s, docs=%d",
            self.property_display_name,
            self.store.document_count,
        )


def create_app_context(settings: Settings | None = None) -> AppContext:
    """Factory that wires everything together."""
    if settings is None:
        settings = Settings()

    documents = load_property_documents(
        property_dir=settings.property_data_dir,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    store = PropertyKnowledgeStore(documents=documents)
    return AppContext(settings=settings, store=store)
