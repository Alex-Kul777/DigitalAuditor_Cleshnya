"""Unit tests for BrinksIndexer."""
import pytest
import json
from pathlib import Path
from knowledge.brinks_indexer import BrinksIndexer
from core.config import PROJECT_ROOT, BRINKS_CHAPTERS_INDEX


class TestBrinksIndexer:
    """Test suite for BrinksIndexer class."""

    @pytest.fixture
    def indexer(self):
        """Create BrinksIndexer instance."""
        return BrinksIndexer()

    def test_indexer_initialization(self, indexer):
        """Test that indexer initializes properly."""
        assert indexer is not None
        assert indexer.embeddings is not None
        assert indexer.text_splitter is not None
        assert indexer.chapters_config is not None

    def test_chapters_config_loaded(self, indexer):
        """Test that chapters config is loaded from JSON."""
        config = indexer.chapters_config
        assert "brinks_modern_internal_auditing" in config
        assert "chapters" in config["brinks_modern_internal_auditing"]
        chapters = config["brinks_modern_internal_auditing"]["chapters"]
        assert len(chapters) > 0

    def test_get_indexed_chapters(self, indexer):
        """Test retrieving list of chapters with include_in_rag=true."""
        chapters = indexer.get_indexed_chapters()
        assert isinstance(chapters, list)
        assert len(chapters) > 0

        # All returned chapters should have these fields
        for ch in chapters:
            assert "number" in ch
            assert "title" in ch
            assert "priority" in ch

    def test_parse_page_range_valid(self, indexer):
        """Test parsing valid page ranges."""
        start, end = indexer._parse_page_range("51-100")
        assert start == 51
        assert end == 100

    def test_parse_page_range_invalid(self, indexer):
        """Test parsing invalid page ranges returns None."""
        start, end = indexer._parse_page_range("invalid")
        assert start is None
        assert end is None

    def test_chapters_config_file_exists(self):
        """Test that brinks_chapters.json exists."""
        config_path = PROJECT_ROOT / BRINKS_CHAPTERS_INDEX
        assert config_path.exists(), f"Config file not found: {config_path}"

    def test_chapters_config_structure(self, indexer):
        """Test that chapters config has required structure."""
        config = indexer.chapters_config["brinks_modern_internal_auditing"]

        # Check top-level fields
        assert "pdf_path" in config
        assert "total_pages" in config
        assert config["total_pages"] > 0
        assert "chunk_size" in config
        assert config["chunk_size"] == 512  # Should match BRINKS_CHUNK_SIZE

    def test_chapters_have_required_fields(self, indexer):
        """Test that each chapter has required metadata fields."""
        chapters = indexer.chapters_config["brinks_modern_internal_auditing"]["chapters"]

        for chapter in chapters:
            assert "number" in chapter
            assert "title" in chapter
            assert "pages" in chapter
            assert "include_in_rag" in chapter
            # Pages should be a string like "51-100"
            assert "-" in chapter["pages"] or chapter["pages"] == "unknown"

    def test_indexed_chapters_have_priority(self, indexer):
        """Test that indexed chapters have priority field."""
        chapters = indexer.get_indexed_chapters()

        valid_priorities = {"critical", "high", "medium", "low"}
        for ch in chapters:
            assert ch["priority"] in valid_priorities

    def test_critical_chapters_in_rag(self, indexer):
        """Test that critical chapters are marked for RAG indexing."""
        config = indexer.chapters_config["brinks_modern_internal_auditing"]
        chapters = config["chapters"]

        critical_chapters = [ch for ch in chapters if ch.get("priority") == "critical"]
        for ch in critical_chapters:
            assert ch.get("include_in_rag", False), \
                f"Critical chapter {ch['number']} not marked for RAG: {ch['title']}"

    def test_pdf_file_exists(self):
        """Test that Brink's PDF file exists."""
        config = BrinksIndexer().chapters_config
        if not config:
            pytest.skip("Chapters config not loaded")

        pdf_path = config.get("brinks_modern_internal_auditing", {}).get("pdf_path")
        if pdf_path:
            full_path = PROJECT_ROOT / pdf_path
            assert full_path.exists(), f"PDF not found: {full_path}"

    def test_at_least_20_chapters_for_rag(self, indexer):
        """Test that at least 20 chapters are marked for RAG indexing."""
        chapters = indexer.get_indexed_chapters()
        assert len(chapters) >= 20, f"Expected 20+ chapters, got {len(chapters)}"

    def test_chapter_page_ranges_cover_full_book(self, indexer):
        """Test that chapter page ranges reasonably cover the full book."""
        config = indexer.chapters_config["brinks_modern_internal_auditing"]
        total_pages = config.get("total_pages", 0)

        # Extract all page numbers from included chapters
        chapters = config["chapters"]
        indexed_chapters = [ch for ch in chapters if ch.get("include_in_rag")]

        if indexed_chapters and total_pages > 0:
            # At least 50% of book should be indexed
            page_coverage = len(indexed_chapters) * 20  # rough estimate
            assert page_coverage > total_pages * 0.5, \
                f"Low page coverage: {page_coverage} / {total_pages}"
