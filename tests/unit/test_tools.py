"""
Unit tests for tools module.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

from tools.evidence_tracker import EvidenceTracker
from tools.risk_matrix import calculate_risk_level


class TestEvidenceTracker:
    """Test EvidenceTracker class."""

    def test_evidence_tracker_initialization(self, tmp_path):
        """Test EvidenceTracker initialization with new task directory."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        assert tracker.evidence_file == task_dir / "evidence" / "evidence_log.json"
        assert tracker.evidence == []

    def test_evidence_tracker_load_existing(self, tmp_path):
        """Test EvidenceTracker loads existing evidence file."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        # Create existing evidence file
        existing_evidence = [
            {
                "timestamp": "2026-04-20T12:00:00",
                "source": "previous_audit",
                "content": "Previous finding",
                "relevance": "High",
            }
        ]
        evidence_file = task_dir / "evidence" / "evidence_log.json"
        evidence_file.write_text(json.dumps(existing_evidence))

        tracker = EvidenceTracker(task_dir)
        assert len(tracker.evidence) == 1
        assert tracker.evidence[0]["source"] == "previous_audit"

    def test_evidence_tracker_add_single(self, tmp_path):
        """Test adding single evidence to tracker."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        tracker.add("test_source", "test content", "High")

        assert len(tracker.evidence) == 1
        assert tracker.evidence[0]["source"] == "test_source"
        assert tracker.evidence[0]["content"] == "test content"
        assert tracker.evidence[0]["relevance"] == "High"

    def test_evidence_tracker_add_multiple(self, tmp_path):
        """Test adding multiple evidence items."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        tracker.add("source1", "content1", "High")
        tracker.add("source2", "content2", "Medium")
        tracker.add("source3", "content3", "Low")

        assert len(tracker.evidence) == 3

    def test_evidence_tracker_persists_to_file(self, tmp_path):
        """Test that evidence is persisted to file."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        tracker.add("test_source", "test content", "High")

        # Read file directly to verify persistence
        evidence_file = task_dir / "evidence" / "evidence_log.json"
        assert evidence_file.exists()
        data = json.loads(evidence_file.read_text())
        assert len(data) == 1
        assert data[0]["source"] == "test_source"

    def test_evidence_tracker_timestamp_format(self, tmp_path):
        """Test that evidence includes ISO format timestamp."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        tracker.add("test_source", "test content", "High")

        # Verify timestamp is ISO format
        timestamp = tracker.evidence[0]["timestamp"]
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Invalid ISO format timestamp: {timestamp}")

    def test_evidence_tracker_unicode_support(self, tmp_path):
        """Test that evidence tracker supports Unicode characters."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        tracker.add("русский_источник", "Содержание на русском языке", "Высокий")

        assert len(tracker.evidence) == 1
        assert tracker.evidence[0]["source"] == "русский_источник"
        assert "русском" in tracker.evidence[0]["content"]

    def test_evidence_tracker_json_format(self, tmp_path):
        """Test that evidence is stored as valid JSON."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        tracker.add("test", "content", "High")

        # Read and parse JSON
        evidence_file = task_dir / "evidence" / "evidence_log.json"
        content = evidence_file.read_text()
        try:
            data = json.loads(content)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            pytest.fail("Evidence file is not valid JSON")

    def test_evidence_tracker_clear_behavior(self, tmp_path):
        """Test creating new tracker reloads from file."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        # First tracker adds evidence
        tracker1 = EvidenceTracker(task_dir)
        tracker1.add("source1", "content1", "High")

        # Second tracker instance reads from same file
        tracker2 = EvidenceTracker(task_dir)
        assert len(tracker2.evidence) == 1
        assert tracker2.evidence[0]["source"] == "source1"


class TestRiskMatrixIntegration:
    """Integration tests for risk matrix with other components."""

    def test_risk_matrix_in_evidence_tracking(self, tmp_path):
        """Test using risk matrix with evidence tracking."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)

        # Add evidence with calculated risk
        risk_level = calculate_risk_level("High", "High")
        tracker.add("security_audit", f"Risk assessment: {risk_level}", "High")

        assert len(tracker.evidence) == 1
        assert "Critical" in tracker.evidence[0]["content"]

    def test_multiple_risk_assessments(self):
        """Test multiple risk assessments for comprehensive audit."""
        assessments = [
            ("High", "High", "Critical"),
            ("High", "Medium", "High"),
            ("Medium", "Low", "Low"),
            ("Low", "High", "Medium"),
        ]

        for prob, impact, expected_risk in assessments:
            actual_risk = calculate_risk_level(prob, impact)
            assert actual_risk == expected_risk, (
                f"Risk({prob}, {impact}) should be {expected_risk}, got {actual_risk}"
            )


class TestToolsImports:
    """Test that all tools can be imported."""

    def test_import_evidence_tracker(self):
        """Test importing EvidenceTracker."""
        assert EvidenceTracker is not None

    def test_import_risk_matrix(self):
        """Test importing risk_matrix."""
        assert calculate_risk_level is not None

    def test_import_web_search(self):
        """Test importing web_search module."""
        from tools import web_search
        assert web_search is not None

    def test_import_file_downloader(self):
        """Test importing file_downloader module."""
        from tools import file_downloader
        assert file_downloader is not None


class TestEvidenceTrackerEdgeCases:
    """Test edge cases in evidence tracking."""

    def test_evidence_with_special_characters(self, tmp_path):
        """Test evidence with special characters."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        special_content = "Content with special chars: @#$%^&*()\n\t\"quotes\""
        tracker.add("special_source", special_content, "High")

        assert len(tracker.evidence) == 1
        assert tracker.evidence[0]["content"] == special_content

    def test_evidence_with_long_content(self, tmp_path):
        """Test evidence with very long content."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        long_content = "A" * 10000
        tracker.add("long_source", long_content, "High")

        assert len(tracker.evidence) == 1
        assert len(tracker.evidence[0]["content"]) == 10000

    def test_evidence_with_empty_content(self, tmp_path):
        """Test evidence with empty content."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        tracker.add("empty_source", "", "Low")

        assert len(tracker.evidence) == 1
        assert tracker.evidence[0]["content"] == ""

    def test_evidence_relevance_levels(self, tmp_path):
        """Test evidence with different relevance levels."""
        task_dir = tmp_path / "test_task"
        task_dir.mkdir()
        (task_dir / "evidence").mkdir()

        tracker = EvidenceTracker(task_dir)
        relevance_levels = ["Critical", "High", "Medium", "Low", "Minimal"]

        for level in relevance_levels:
            tracker.add("source", f"Content with {level} relevance", level)

        assert len(tracker.evidence) == len(relevance_levels)
        stored_levels = [e["relevance"] for e in tracker.evidence]
        assert stored_levels == relevance_levels


@pytest.mark.unit
class TestToolsMarker:
    """Test tools module with unit marker."""

    def test_all_tool_modules_exist(self):
        """Verify all expected tool modules exist."""
        from tools import (
            evidence_tracker,
            risk_matrix,
            web_search,
            file_downloader,
        )
        assert evidence_tracker is not None
        assert risk_matrix is not None
        assert web_search is not None
        assert file_downloader is not None
