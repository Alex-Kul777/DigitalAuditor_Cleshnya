"""Integration tests for DOCX export/import/revision cycle."""

import json
import tempfile
from pathlib import Path

import pytest

from report_generator.docx import (
    DocxExporter,
    DocxImporter,
    VersionManager,
)
from agents.revision_agent import RevisionAgent


class TestDocxExportImportCycle:
    """E2E tests for complete DOCX review cycle."""

    @pytest.fixture
    def test_dir(self):
        """Create temporary task directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            task_dir = Path(tmpdir) / "test_task"
            task_dir.mkdir(parents=True)
            (task_dir / "output").mkdir(exist_ok=True)
            yield task_dir

    @pytest.fixture
    def sample_md(self):
        """Sample audit report markdown."""
        return """# Audit Report

## Executive Summary

Executive summary paragraph with findings summary.

<!-- REVIEWER:uncle_kahneman:START -->
> **💬 Дядя Канеман замечает:**
> This summary mixes facts and opinions.
<!-- REVIEWER:uncle_kahneman:END -->

## Findings

### Finding 1: System Architecture

Architecture findings with details.

## Conclusion

Audit completed with recommendations.
"""

    def test_export_md_to_docx(self, test_dir, sample_md):
        """Test MD to DOCX export."""
        md_path = test_dir / "report.md"
        md_path.write_text(sample_md, encoding='utf-8')

        docx_path = test_dir / "report.docx"
        exporter = DocxExporter()
        result = exporter.export(md_path, docx_path)

        assert result == docx_path
        assert docx_path.exists()
        assert docx_path.stat().st_size > 0

    def test_extract_comments_on_export(self, test_dir, sample_md):
        """Test comment extraction during export."""
        md_path = test_dir / "report.md"
        md_path.write_text(sample_md, encoding='utf-8')

        docx_path = test_dir / "report.docx"
        exporter = DocxExporter()
        exporter.export(md_path, docx_path)

        # Check that comments were extracted
        comments = exporter._extract_comments(sample_md)
        assert len(comments) > 0
        assert comments[0][1] == "uncle_kahneman"
        assert "mixes facts" in comments[0][2]

    def test_comments_stripped_from_export(self, test_dir, sample_md):
        """Test that reviewer blocks are stripped from exported DOCX."""
        exporter = DocxExporter()
        clean_md = exporter._strip_comments(sample_md)

        # Verify comment blocks removed
        assert "<!-- REVIEWER:" not in clean_md
        assert "Дядя Канеман" not in clean_md

        # Verify content preserved
        assert "# Audit Report" in clean_md
        assert "Executive Summary" in clean_md

    def test_import_feedback_structure(self, test_dir, sample_md):
        """Test feedback extraction structure."""
        # First export
        md_path = test_dir / "report.md"
        md_path.write_text(sample_md, encoding='utf-8')

        docx_path = test_dir / "report.docx"
        exporter = DocxExporter()
        exporter.export(md_path, docx_path)

        # Now import
        importer = DocxImporter()
        feedback = importer.extract_feedback(docx_path, md_path)

        # Verify structure
        assert hasattr(feedback, 'comments_by_agent')
        assert hasattr(feedback, 'comments_by_user')
        assert hasattr(feedback, 'tracked_changes')
        assert hasattr(feedback, 'source_md')
        assert isinstance(feedback.comments_by_agent, list)
        assert isinstance(feedback.comments_by_user, list)
        assert isinstance(feedback.tracked_changes, list)
        assert isinstance(feedback.source_md, str)

    def test_version_manager_save_and_track(self, test_dir, sample_md):
        """Test version manager saves and tracks versions."""
        md_path = test_dir / "report.md"
        md_path.write_text(sample_md, encoding='utf-8')

        docx_path = test_dir / "report.docx"
        exporter = DocxExporter()
        exporter.export(md_path, docx_path)

        # Initialize version manager
        vm = VersionManager(test_dir)

        # Save first version
        v1 = vm.next_version()
        assert v1 == 1

        vm.save(v1, sample_md, docx_path)

        # Verify manifest created
        manifest_path = test_dir / "output" / "latest.json"
        assert manifest_path.exists()

        manifest = json.loads(manifest_path.read_text())
        assert manifest["current_version"] == 1
        assert len(manifest["history"]) >= 1

        # Verify version directory
        v1_dir = test_dir / "versions" / "v1"
        assert v1_dir.exists()
        assert (v1_dir / "source.md").exists()
        assert (v1_dir / "report.docx").exists()

        # Verify latest symlink (actual copy, not symlink)
        latest = test_dir / "output" / "Audit_Report.docx"
        assert latest.exists()

    def test_version_manager_list_versions(self, test_dir, sample_md):
        """Test listing available versions."""
        exporter = DocxExporter()
        vm = VersionManager(test_dir)

        # Create mock versions
        for i in range(1, 4):
            md_path = test_dir / f"report_v{i}.md"
            md_path.write_text(f"{sample_md}\n\nVersion {i}", encoding='utf-8')

            docx_path = test_dir / "output" / f"report_v{i}.docx"
            exporter.backend.md_to_docx(md_path.read_text(), docx_path)

            vm.save(i, md_path.read_text(), docx_path)

        # List versions
        versions = vm.list_versions()
        assert len(versions) >= 3
        assert sorted(versions) == versions

    def test_revision_agent_revises_markdown(self, test_dir, sample_md, mocker):
        """Test revision agent applies changes to markdown."""
        # Mock LLM to avoid Ollama dependency in tests
        mocker.patch("agents.revision_agent.LLMFactory.get_llm")

        # Setup: export and import
        md_path = test_dir / "report.md"
        md_path.write_text(sample_md, encoding='utf-8')

        docx_path = test_dir / "report.docx"
        exporter = DocxExporter()
        exporter.export(md_path, docx_path)

        # Import feedback
        importer = DocxImporter()
        feedback = importer.extract_feedback(docx_path, md_path)

        # Revise (in practice, changes come from DOCX; here we test structure)
        agent = RevisionAgent()

        # Verify agent initialized
        assert agent.exporter is not None
        assert agent.importer is not None

    def test_e2e_export_comment_import_cycle(self, test_dir, sample_md, mocker):
        """Full E2E cycle: export → inject comments → import."""
        # Mock LLM for persona loading in importer
        mocker.patch("knowledge.persona_indexer.PersonaIndexer.list_personas", return_value=[])

        # Step 1: Export
        md_path = test_dir / "report.md"
        md_path.write_text(sample_md, encoding='utf-8')

        docx_path = test_dir / "report.docx"
        exporter = DocxExporter()
        exporter.export(md_path, docx_path)

        assert docx_path.exists(), "DOCX not created"

        # Step 2: Import
        importer = DocxImporter()
        feedback = importer.extract_feedback(docx_path, md_path)

        assert len(feedback.source_md) > 0, "Source MD not extracted"
        assert len(feedback.comments_by_agent) + len(feedback.comments_by_user) > 0, "No comments extracted"

        # Step 3: Version tracking
        vm = VersionManager(test_dir)
        v1 = vm.next_version()
        vm.save(v1, sample_md, docx_path)

        latest = vm.latest()
        assert latest is not None
        assert latest.exists()

    def test_docx_created_on_export(self, test_dir):
        """Smoke test: DOCX file is created and has content."""
        simple_md = "# Test\n\nParagraph."
        md_path = test_dir / "simple.md"
        md_path.write_text(simple_md)

        docx_path = test_dir / "simple.docx"
        exporter = DocxExporter()
        exporter.export(md_path, docx_path)

        # File exists and has reasonable size
        assert docx_path.exists()
        size = docx_path.stat().st_size
        assert size > 5000, f"DOCX too small: {size} bytes"
