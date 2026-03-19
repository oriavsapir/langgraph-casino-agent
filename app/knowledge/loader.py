import logging
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def load_property_documents(
    property_dir: Path,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
) -> list[Document]:
    """Load all markdown files from a property directory, chunk them, and return
    a list of LangChain ``Document`` objects enriched with metadata."""

    if not property_dir.is_dir():
        raise FileNotFoundError(
            f"Property data directory not found: {property_dir}"
        )

    md_files = sorted(property_dir.glob("*.md"))
    if not md_files:
        raise ValueError(f"No markdown files found in {property_dir}")

    property_id = property_dir.name
    raw_documents: list[Document] = []

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        category = md_file.stem
        raw_documents.append(
            Document(
                page_content=text,
                metadata={
                    "property_id": property_id,
                    "category": category,
                    "source_file": md_file.name,
                },
            )
        )

    splitter = _build_markdown_splitter(chunk_size, chunk_overlap)
    chunks = splitter.split_documents(raw_documents)

    for chunk in chunks:
        section = _extract_nearest_heading(chunk.page_content)
        if section:
            chunk.metadata["section"] = section

    logger.info(
        "Loaded %d chunks from %d files for property '%s'",
        len(chunks),
        len(md_files),
        property_id,
    )
    return chunks


def _build_markdown_splitter(
    chunk_size: int, chunk_overlap: int
) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter.from_language(
        language=Language.MARKDOWN,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def _extract_nearest_heading(text: str) -> str | None:
    """Return the first markdown heading found in the chunk text."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return None
