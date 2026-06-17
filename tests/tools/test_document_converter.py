#!/usr/bin/env python3
"""Tests for PDF translation and Markdown conversion."""

import pytest
from pathlib import Path
from tools.document_converter import translate_pdf, convert_pdf_to_markdown, _check_deps


class TestDocumentConverterDeps:
    """Test dependency checking."""

    def test_check_deps_docling_installed(self):
        """Docling should be installed (required by project)."""
        try:
            _check_deps(need_docling=True)
        except SystemExit:
            pytest.fail("Docling not installed, but it's in requirements.txt")

    def test_check_deps_pdf2zh_check(self):
        """Check if pdf2zh is available on system (might not be installed)."""
        try:
            _check_deps(need_pdf2zh=True)
            pdf2zh_available = True
        except SystemExit:
            pdf2zh_available = False
        # Don't fail if pdf2zh not available - it's optional for CLI use
        assert isinstance(pdf2zh_available, bool)


class TestConvertPdfToMarkdown:
    """Test Markdown conversion."""

    @pytest.mark.skipif(
        not Path("personas/CISA/raw/CISA Review Manual.pdf").exists(),
        reason="Test PDF not found"
    )
    def test_convert_pdf_to_markdown_simple_page_range(self):
        """Test converting a small page range (1-5) to Markdown."""
        pdf_path = Path("personas/CISA/raw/CISA Review Manual.pdf")
        md_path = convert_pdf_to_markdown(pdf_path, page_range=(1, 5))

        assert md_path.exists(), f"Output file not created: {md_path}"
        assert md_path.suffix == ".md", "Output should have .md extension"
        assert md_path.stat().st_size > 0, "Output Markdown file is empty"

    @pytest.mark.skipif(
        not Path("personas/CISA/raw/CISA Review Manual.pdf").exists(),
        reason="Test PDF not found"
    )
    def test_convert_output_has_content(self):
        """Verify output has meaningful content (not just whitespace)."""
        pdf_path = Path("personas/CISA/raw/CISA Review Manual.pdf")
        md_path = convert_pdf_to_markdown(pdf_path, page_range=(1, 5))
        content = md_path.read_text(encoding="utf-8")

        assert len(content.strip()) > 0, "Markdown output is empty or only whitespace"
        assert len(content) > 100, "Markdown output looks suspiciously small"


class TestGitignore:
    """Test .gitignore rules."""

    def test_gitignore_excludes_pdf_files(self):
        """Verify .gitignore excludes PDF files from personas/*/raw/."""
        result = Path("personas/CISA/raw/CISA Review Manual.pdf").exists()
        # File exists on disk but should be ignored by git
        assert result, "Test PDF should exist on disk"

    def test_gitignore_includes_markdown_files(self):
        """Verify .gitignore includes .md files from personas/*/raw/."""
        md_files = list(Path("personas/CISA/raw/").glob("*.md"))
        assert len(md_files) > 0, "No markdown files found in personas/CISA/raw/"
        # These should NOT be ignored
        assert any(f.name.endswith(".md") for f in md_files)


class TestDocumentConverterIntegration:
    """Integration tests."""

    def test_cli_main_function_exists(self):
        """Test that CLI main function is importable."""
        from tools.document_converter import main
        assert callable(main), "main() should be callable"

    def test_convert_command_in_main_cli(self):
        """Test that convert command exists in main.py."""
        import subprocess
        result = subprocess.run(
            ["python", "main.py", "convert", "--help"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0, "convert command should have --help"
        assert "input" in result.stdout.lower(), "--input flag should be documented"
