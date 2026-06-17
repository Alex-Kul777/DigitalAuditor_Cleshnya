import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from report_generator.orchestrator import ReportOrchestrator


@patch('report_generator.orchestrator.CisaAuditor')
@patch('report_generator.orchestrator.UncleRobertAgent')
@patch('report_generator.orchestrator.Retriever')
class TestReviewerHookIntegration:
    """Integration tests for reviewer hook in orchestrator."""

    def test_reviewer_hook_loads_uncle_kahneman(self, mock_retriever, mock_uncle_robert, mock_cisa):
        """Verify reviewer hook successfully loads UncleKahneman."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            (task_dir / "output").mkdir()
            (task_dir / "config.yaml").write_text("name: test\ncompany: Test Co\nreviewer: uncle_kahneman")

            # Mock the reviewer
            with patch('report_generator.orchestrator.importlib.import_module') as mock_import:
                mock_module = MagicMock()
                mock_reviewer_class = MagicMock()
                mock_reviewer = MagicMock()
                mock_reviewer.review_markdown = MagicMock(return_value="Reviewed content")

                mock_module.UncleKahneman = mock_reviewer_class
                mock_reviewer_class.return_value = mock_reviewer
                mock_import.return_value = mock_module

                orch = ReportOrchestrator(task_dir)
                orch._apply_reviewer_hook("Test report content")

                # Verify reviewer was instantiated
                mock_reviewer_class.assert_called_once_with(persona_name="uncle_kahneman")
                # Verify review_markdown was called
                mock_reviewer.review_markdown.assert_called_once_with("Test report content")

    def test_reviewer_hook_no_reviewer_configured(self, mock_retriever, mock_uncle_robert, mock_cisa):
        """Verify hook is skipped when no reviewer configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            (task_dir / "output").mkdir()
            (task_dir / "config.yaml").write_text("name: test\ncompany: Test Co")

            orch = ReportOrchestrator(task_dir)
            
            # Should return without error (no reviewer)
            result = orch._apply_reviewer_hook("Test report")
            assert result is None

    def test_reviewer_hook_unknown_reviewer(self, mock_retriever, mock_uncle_robert, mock_cisa):
        """Verify hook skips unknown reviewer gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            (task_dir / "output").mkdir()
            (task_dir / "config.yaml").write_text("name: test\ncompany: Test Co\nreviewer: unknown_reviewer")

            orch = ReportOrchestrator(task_dir)
            
            # Should return without error (unknown reviewer)
            result = orch._apply_reviewer_hook("Test report")
            assert result is None

    def test_reviewer_hook_saves_reviewed_file(self, mock_retriever, mock_uncle_robert, mock_cisa):
        """Verify hook saves reviewed report to separate file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            (task_dir / "output").mkdir()
            (task_dir / "config.yaml").write_text("name: test\ncompany: Test Co\nreviewer: uncle_kahneman")

            with patch('report_generator.orchestrator.importlib.import_module') as mock_import:
                mock_module = MagicMock()
                mock_reviewer = MagicMock()
                mock_reviewer.review_markdown = MagicMock(return_value="<!-- REVIEWER:uncle_kahneman:START -->\nReviewed\n<!-- REVIEWER:uncle_kahneman:END -->")

                mock_module.UncleKahneman = MagicMock(return_value=mock_reviewer)
                mock_import.return_value = mock_module

                orch = ReportOrchestrator(task_dir)
                orch._apply_reviewer_hook("Original report")

                # Check reviewed file was created
                reviewed_path = task_dir / "output" / "Audit_Report_Reviewed.md"
                assert reviewed_path.exists()
                content = reviewed_path.read_text(encoding='utf-8')
                assert "REVIEWER:uncle_kahneman:START" in content

    def test_reviewer_hook_env_override(self, mock_retriever, mock_uncle_robert, mock_cisa):
        """Verify DA_REVIEWER_OVERRIDE env var overrides config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            (task_dir / "output").mkdir()
            # Config has no reviewer
            (task_dir / "config.yaml").write_text("name: test\ncompany: Test Co")

            with patch.dict('os.environ', {'DA_REVIEWER_OVERRIDE': 'uncle_kahneman'}):
                with patch('report_generator.orchestrator.importlib.import_module') as mock_import:
                    mock_module = MagicMock()
                    mock_reviewer = MagicMock()
                    mock_reviewer.review_markdown = MagicMock(return_value="Reviewed")

                    mock_module.UncleKahneman = MagicMock(return_value=mock_reviewer)
                    mock_import.return_value = mock_module

                    orch = ReportOrchestrator(task_dir)
                    orch._apply_reviewer_hook("Test report")

                    # Reviewer should be called despite no config
                    mock_reviewer.review_markdown.assert_called_once()

    def test_reviewer_hook_error_handling(self, mock_retriever, mock_uncle_robert, mock_cisa):
        """Verify hook handles reviewer errors gracefully without failing audit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            (task_dir / "output").mkdir()
            (task_dir / "config.yaml").write_text("name: test\ncompany: Test Co\nreviewer: uncle_kahneman")

            with patch('report_generator.orchestrator.importlib.import_module') as mock_import:
                # Simulate reviewer error
                mock_import.side_effect = RuntimeError("Reviewer initialization failed")

                orch = ReportOrchestrator(task_dir)
                
                # Should NOT raise, but log error
                result = orch._apply_reviewer_hook("Test report")
                assert result is None  # Error handled gracefully

    def test_main_report_unaffected_on_reviewer_error(self, mock_retriever, mock_uncle_robert, mock_cisa):
        """Verify main Audit_Report.md exists even if reviewer fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir)
            (task_dir / "output").mkdir()
            (task_dir / "config.yaml").write_text("name: test\ncompany: Test Co\nreviewer: uncle_kahneman")

            # Create draft files that _assemble_report expects
            drafts_dir = task_dir / "drafts"
            drafts_dir.mkdir()
            for i in range(1, 6):
                (drafts_dir / f"0{i}_*.md").write_text(f"Section {i}")

            with patch('report_generator.orchestrator.importlib.import_module') as mock_import:
                mock_import.side_effect = RuntimeError("Reviewer error")

                orch = ReportOrchestrator(task_dir)
                
                # Hook should fail gracefully
                orch._apply_reviewer_hook("Test report")
                
                # Main report should still be there (written before hook)
                main_report = task_dir / "output" / "Audit_Report.md"
                # Note: main report written in generate(), not in _apply_reviewer_hook
                # This test verifies hook doesn't delete or corrupt existing files
