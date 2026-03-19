"""Tests for the property document loader."""

from pathlib import Path

import pytest

from app.knowledge.loader import load_property_documents, _extract_nearest_heading


class TestLoadPropertyDocuments:
    def test_loads_chunks_from_real_property(self, property_dir: Path):
        docs = load_property_documents(property_dir, chunk_size=800, chunk_overlap=200)
        assert len(docs) > 0
        for doc in docs:
            assert doc.metadata["property_id"] == "mohegan_sun"
            assert doc.metadata["category"] in {
                "overview", "dining", "entertainment", "hotel",
                "gaming", "amenities", "promotions", "practical_info",
            }

    def test_all_categories_represented(self, property_dir: Path):
        docs = load_property_documents(property_dir)
        categories = {doc.metadata["category"] for doc in docs}
        expected = {"overview", "dining", "entertainment", "hotel", "gaming", "amenities", "promotions", "practical_info"}
        assert categories == expected

    def test_chunks_are_within_size_limit(self, property_dir: Path):
        chunk_size = 800
        docs = load_property_documents(property_dir, chunk_size=chunk_size, chunk_overlap=200)
        for doc in docs:
            assert len(doc.page_content) <= chunk_size * 1.5

    def test_missing_directory_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_property_documents(tmp_path / "nonexistent")

    def test_empty_directory_raises(self, tmp_path: Path):
        empty_dir = tmp_path / "empty_property"
        empty_dir.mkdir()
        with pytest.raises(ValueError, match="No markdown files"):
            load_property_documents(empty_dir)


class TestExtractNearestHeading:
    def test_extracts_h1(self):
        assert _extract_nearest_heading("# Overview\nSome text") == "Overview"

    def test_extracts_h2(self):
        assert _extract_nearest_heading("## Fine Dining\nDetails here") == "Fine Dining"

    def test_extracts_h3(self):
        assert _extract_nearest_heading("### Sky Tower Suite\nLuxury") == "Sky Tower Suite"

    def test_returns_none_when_no_heading(self):
        assert _extract_nearest_heading("Just plain text\nno headings") is None

    def test_returns_first_heading(self):
        text = "Some preamble\n## First\n### Second"
        assert _extract_nearest_heading(text) == "First"
