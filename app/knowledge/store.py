import logging

import chromadb
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

COLLECTION_NAME = "property_knowledge"


class PropertyKnowledgeStore:
    """Thin wrapper around ChromaDB for property-specific document retrieval.

    Uses ChromaDB's built-in default embedding function so the application
    can start without an OpenAI key for embedding (ChromaDB ships with a
    lightweight local embedding model).  For production workloads this can
    be swapped out for OpenAI or any other embedding provider.
    """

    def __init__(self, documents: list[Document] | None = None) -> None:
        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        if documents:
            self._ingest(documents)

    def _ingest(self, documents: list[Document]) -> None:
        if not documents:
            return

        ids = [f"doc-{i}" for i in range(len(documents))]
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        self._collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info("Ingested %d documents into vector store", len(documents))

    def search(self, query: str, k: int = 6) -> list[Document]:
        """Semantic similarity search returning the top-*k* documents."""
        total = self._collection.count()
        if total == 0:
            return []

        results = self._collection.query(
            query_texts=[query],
            n_results=min(k, total),
        )

        documents: list[Document] = []
        for text, metadata in zip(
            results["documents"][0],
            results["metadatas"][0],
        ):
            documents.append(Document(page_content=text, metadata=metadata))
        return documents

    @property
    def document_count(self) -> int:
        return self._collection.count()
