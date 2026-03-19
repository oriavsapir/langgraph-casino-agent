"""Shared fixtures for the test suite."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage

from app.knowledge.store import PropertyKnowledgeStore

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PROPERTY_DIR = Path(__file__).resolve().parent.parent / "app" / "data" / "properties" / "mohegan_sun"


@pytest.fixture()
def sample_documents() -> list[Document]:
    return [
        Document(
            page_content="Todd English's Tuscany serves Italian cuisine in Casino of the Sky. "
            "Hours: Wednesday–Sunday 5 PM – 10 PM. Price range: $$$$.",
            metadata={"property_id": "mohegan_sun", "category": "dining", "section": "Todd English's Tuscany"},
        ),
        Document(
            page_content="The Mohegan Sun Arena seats 10,000 and hosts major concerts, "
            "boxing, UFC events, and comedy specials.",
            metadata={"property_id": "mohegan_sun", "category": "entertainment", "section": "Mohegan Sun Arena"},
        ),
        Document(
            page_content="Sky Tower Deluxe King Room: 450 sq ft, king bed, marble bathroom, "
            "starting from $249/night.",
            metadata={"property_id": "mohegan_sun", "category": "hotel", "section": "Deluxe King Room"},
        ),
        Document(
            page_content="Mohegan Sun is located at 1 Mohegan Sun Boulevard, Uncasville, CT 06382. "
            "Self-parking is complimentary.",
            metadata={"property_id": "mohegan_sun", "category": "overview", "section": "Location & Address"},
        ),
        Document(
            page_content="The poker room has 42 tables, open 24/7. No-Limit Texas Hold'em "
            "stakes from $1/$2 to $25/$50.",
            metadata={"property_id": "mohegan_sun", "category": "gaming", "section": "Poker Room"},
        ),
    ]


@pytest.fixture()
def knowledge_store(sample_documents: list[Document]) -> PropertyKnowledgeStore:
    return PropertyKnowledgeStore(documents=sample_documents)


@pytest.fixture()
def mock_llm() -> MagicMock:
    """A mocked ChatOpenAI whose ``ainvoke`` can be configured per-test."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(
        return_value=AIMessage(content='{"intent": "property_question"}')
    )
    return llm


@pytest.fixture()
def property_dir() -> Path:
    return PROPERTY_DIR
