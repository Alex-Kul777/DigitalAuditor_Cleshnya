import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from knowledge.evidence_indexer import EvidenceIndexer


class TestEvidenceIndexerSync:
    """Test evidence indexing with SHA-256 tracking."""

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_creates_state_file(self, mock_indexer_class):
        """Verify sync creates .index_state.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)

            # Create a test evidence file
            test_file = evidence_dir / "test_evidence.txt"
            test_file.write_text("Test evidence content")

            # Mock the indexer
            mock_indexer = MagicMock()
            mock_indexer.index_file.return_value = 10
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            indexer.sync()

            state_file = evidence_dir / ".index_state.json"
            assert state_file.exists()

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_records_sha256(self, mock_indexer_class):
        """Verify sync records SHA-256 hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            test_file = evidence_dir / "evidence.txt"
            test_file.write_text("Content")

            mock_indexer = MagicMock()
            mock_indexer.index_file.return_value = 5
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            indexer.sync()

            state = json.loads((evidence_dir / ".index_state.json").read_text())
            assert "evidence.txt" in state
            assert "sha256" in state["evidence.txt"]
            assert len(state["evidence.txt"]["sha256"]) == 64

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_skips_unchanged_files(self, mock_indexer_class):
        """Verify unchanged files are not re-indexed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            test_file = evidence_dir / "evidence.txt"
            test_file.write_text("Original content")

            mock_indexer = MagicMock()
            mock_indexer.index_file.return_value = 5
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            result1 = indexer.sync()
            assert "evidence.txt" in result1

            result2 = indexer.sync()
            assert "evidence.txt" not in result2

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_reindexes_changed_files(self, mock_indexer_class):
        """Verify changed files are re-indexed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            test_file = evidence_dir / "evidence.txt"
            test_file.write_text("Original")

            mock_indexer = MagicMock()
            mock_indexer.index_file.return_value = 5
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            result1 = indexer.sync()
            assert "evidence.txt" in result1

            test_file.write_text("Modified content")
            result2 = indexer.sync()
            assert "evidence.txt" in result2

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_skips_state_file(self, mock_indexer_class):
        """Verify .index_state.json is not indexed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)

            mock_indexer = MagicMock()
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            indexer.sync()

            state = json.loads((evidence_dir / ".index_state.json").read_text())
            assert ".index_state.json" not in state

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_skips_sources_txt(self, mock_indexer_class):
        """Verify sources.txt is not indexed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            (evidence_dir / "sources.txt").write_text("Query 1\nQuery 2")

            mock_indexer = MagicMock()
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            indexer.sync()

            state = json.loads((evidence_dir / ".index_state.json").read_text())
            assert "sources.txt" not in state

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_skips_directories(self, mock_indexer_class):
        """Verify subdirectories are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            subdir = evidence_dir / "subdir"
            subdir.mkdir()
            (subdir / "file.txt").write_text("content")

            mock_indexer = MagicMock()
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            result = indexer.sync()
            assert "subdir" not in result

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_returns_chunk_counts(self, mock_indexer_class):
        """Verify sync returns chunk counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            test_file = evidence_dir / "evidence.txt"
            test_file.write_text("Content for indexing")

            mock_indexer = MagicMock()
            mock_indexer.index_file.return_value = 15
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            result = indexer.sync()

            assert isinstance(result, dict)
            assert "evidence.txt" in result
            assert result["evidence.txt"] == 15

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_empty_directory(self, mock_indexer_class):
        """Verify sync handles empty evidence directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)

            mock_indexer = MagicMock()
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            result = indexer.sync()

            assert result == {}
            assert (evidence_dir / ".index_state.json").exists()

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_records_indexed_timestamp(self, mock_indexer_class):
        """Verify sync records indexed_at timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            test_file = evidence_dir / "evidence.txt"
            test_file.write_text("Content")

            mock_indexer = MagicMock()
            mock_indexer.index_file.return_value = 5
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            indexer.sync()

            state = json.loads((evidence_dir / ".index_state.json").read_text())
            assert "indexed_at" in state["evidence.txt"]


class TestEvidenceIndexerStatus:
    """Test status reporting."""

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_get_status_returns_dict(self, mock_indexer_class):
        """Verify get_status returns dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            mock_indexer_class.return_value = MagicMock()

            indexer = EvidenceIndexer("test_task", evidence_dir)
            status = indexer.get_status()

            assert isinstance(status, dict)

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_get_status_has_task_name(self, mock_indexer_class):
        """Verify status includes task_name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            mock_indexer_class.return_value = MagicMock()

            indexer = EvidenceIndexer("my_task", evidence_dir)
            status = indexer.get_status()

            assert status["task_name"] == "my_task"

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_get_status_counts_files(self, mock_indexer_class):
        """Verify status counts evidence files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            (evidence_dir / "file1.txt").write_text("content1")
            (evidence_dir / "file2.txt").write_text("content2")
            mock_indexer_class.return_value = MagicMock()

            indexer = EvidenceIndexer("test_task", evidence_dir)
            status = indexer.get_status()

            assert status["total_files"] == 2

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_get_status_excludes_skipped_files(self, mock_indexer_class):
        """Verify status excludes .index_state.json and sources.txt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            (evidence_dir / "evidence.txt").write_text("content")
            (evidence_dir / ".index_state.json").write_text("{}")
            (evidence_dir / "sources.txt").write_text("query")
            mock_indexer_class.return_value = MagicMock()

            indexer = EvidenceIndexer("test_task", evidence_dir)
            status = indexer.get_status()

            assert status["total_files"] == 1


class TestEvidenceIndexerMultipleFiles:
    """Test handling multiple evidence files."""

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_multiple_files(self, mock_indexer_class):
        """Verify sync handles multiple evidence files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            (evidence_dir / "file1.txt").write_text("content1")
            (evidence_dir / "file2.txt").write_text("content2")
            (evidence_dir / "file3.txt").write_text("content3")

            mock_indexer = MagicMock()
            mock_indexer.index_file.return_value = 5
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            result = indexer.sync()

            assert len(result) == 3
            assert "file1.txt" in result
            assert "file2.txt" in result
            assert "file3.txt" in result

    @patch('knowledge.evidence_indexer.VectorIndexer')
    def test_sync_partial_changes(self, mock_indexer_class):
        """Verify sync handles partial changes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            evidence_dir = Path(tmpdir)
            file1 = evidence_dir / "file1.txt"
            file2 = evidence_dir / "file2.txt"
            file1.write_text("content1")
            file2.write_text("content2")

            mock_indexer = MagicMock()
            mock_indexer.index_file.return_value = 5
            mock_indexer_class.return_value = mock_indexer

            indexer = EvidenceIndexer("test_task", evidence_dir)
            result1 = indexer.sync()
            assert len(result1) == 2

            file1.write_text("modified1")
            result2 = indexer.sync()
            assert len(result2) == 1
            assert "file1.txt" in result2
            assert "file2.txt" not in result2
