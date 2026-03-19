"""Tests for the PropertyKnowledgeStore."""

from langchain_core.documents import Document

from app.knowledge.store import PropertyKnowledgeStore


class TestPropertyKnowledgeStore:
    def test_document_count(self, knowledge_store: PropertyKnowledgeStore):
        assert knowledge_store.document_count == 5

    def test_search_returns_documents(self, knowledge_store: PropertyKnowledgeStore):
        results = knowledge_store.search("Italian restaurant", k=3)
        assert len(results) > 0
        assert all(isinstance(doc, Document) for doc in results)

    def test_search_respects_k(self, knowledge_store: PropertyKnowledgeStore):
        results = knowledge_store.search("hotel rooms", k=2)
        assert len(results) <= 2

    def test_search_results_have_metadata(self, knowledge_store: PropertyKnowledgeStore):
        results = knowledge_store.search("poker", k=1)
        assert results[0].metadata["property_id"] == "mohegan_sun"

    def test_search_relevance(self, knowledge_store: PropertyKnowledgeStore):
        results = knowledge_store.search("Where can I play poker?", k=2)
        contents = " ".join(doc.page_content for doc in results)
        assert "poker" in contents.lower()

    def test_empty_store(self):
        store = PropertyKnowledgeStore(documents=[])
        assert store.document_count == 0

    def test_empty_store_search(self):
        store = PropertyKnowledgeStore(documents=[])
        results = store.search("anything", k=3)
        assert results == []
