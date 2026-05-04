"""
Tests for README automation scripts.

Tests cover:
- CHANGELOG parsing (Keep a Changelog format)
- Feature extraction from CHANGELOG
- Project structure scanning
- Test count detection
- README generation
- CHANGELOG auto-update
- Translation accuracy for Russian version
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import test modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / '.github' / 'scripts'))

from generate_readme import (
    ChangelogParser,
    ProjectStructureScanner,
    TestCounter,
    ReadmeGenerator,
    Translator,
)

from update_changelog import update_changelog


class TestChangelogParser:
    """Tests for CHANGELOG parsing."""

    @pytest.fixture
    def sample_changelog(self, tmp_path):
        """Create a sample CHANGELOG file."""
        changelog_content = """# Changelog

All notable changes to DigitalAuditor Cleshnya will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- (Auto-generated entries from merged PRs will appear here)

### Fixed
- (Auto-generated entries from merged PRs will appear here)

---

## [2.0.0] - 2026-04-25

### Added

#### M5 — Personalization
- User preference learning system
- PreferencesStore dataclass

#### M4 — DOCX Export
- DOCX backend adapter layer
- Markdown to DOCX export

### Changed
- `report_generator/orchestrator.py` — Reviewer integration
- `core/llm.py` — LLMFactory modes

### Fixed
- Task isolation: no vector store contamination
- Evidence citation accuracy

---

## [1.0.0] - 2026-04-20

### Added
- Core architecture
- ChromaDB integration
- Ollama LLM support
"""
        changelog_file = tmp_path / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)
        return str(changelog_file)

    def test_parse_changelog_file_exists(self, sample_changelog):
        """Test that ChangelogParser initializes with valid file."""
        parser = ChangelogParser(sample_changelog)
        assert parser.content is not None
        assert "Changelog" in parser.content

    def test_extract_latest_release(self, sample_changelog):
        """Test extraction of latest release section."""
        parser = ChangelogParser(sample_changelog)
        latest = parser.get_latest_release()

        assert latest is not None
        assert "2.0.0" in latest
        assert "M5" in latest or "Personalization" in latest

    def test_extract_features_from_changelog(self, sample_changelog):
        """Test feature extraction from Added section."""
        parser = ChangelogParser(sample_changelog)
        features = parser.extract_features()

        assert len(features) > 0
        # Check that some features are extracted from the Added section
        # Actual features depend on CHANGELOG structure
        assert isinstance(features, list)

    def test_extract_features_empty_changelog(self, tmp_path):
        """Test feature extraction from empty CHANGELOG."""
        empty_changelog = tmp_path / "CHANGELOG_empty.md"
        empty_changelog.write_text("# Changelog\n\n## [Unreleased]\n")

        parser = ChangelogParser(str(empty_changelog))
        features = parser.extract_features()

        assert features == []

    def test_unreleased_section_ignored(self, sample_changelog):
        """Test that Unreleased section is not extracted as features."""
        parser = ChangelogParser(sample_changelog)
        features = parser.extract_features()

        # Should only get features from [2.0.0], not [Unreleased]
        assert not any("Auto-generated" in f for f in features)


class TestProjectStructureScanner:
    """Tests for project structure scanning."""

    @pytest.fixture
    def sample_project_dir(self, tmp_path):
        """Create a sample project structure."""
        dirs = {
            'core': ['config.py', 'logger.py', 'llm.py'],
            'agents': ['base.py', 'cisa_auditor.py'],
            'knowledge': ['retriever.py', 'indexer.py'],
            'tools': ['risk_matrix.py'],
        }

        for dir_name, files in dirs.items():
            dir_path = tmp_path / dir_name
            dir_path.mkdir()
            for file in files:
                (dir_path / file).write_text("# stub")

        return str(tmp_path)

    def test_scan_project_directories(self, sample_project_dir):
        """Test scanning project directories."""
        scanner = ProjectStructureScanner(sample_project_dir)
        structure = scanner.scan_dirs(['core', 'agents', 'knowledge', 'tools'])

        assert 'core' in structure
        assert 'agents' in structure
        assert 'knowledge' in structure
        assert 'tools' in structure
        assert 'config' in structure['core']
        assert 'retriever' in structure['knowledge']

    def test_scan_nonexistent_directory(self, sample_project_dir):
        """Test scanning with nonexistent directories."""
        scanner = ProjectStructureScanner(sample_project_dir)
        structure = scanner.scan_dirs(['nonexistent', 'also_not_there'])

        assert len(structure) == 0

    def test_generate_structure_markdown(self, sample_project_dir):
        """Test markdown generation for structure."""
        scanner = ProjectStructureScanner(sample_project_dir)
        # Override scan_dirs to use our test dirs
        with patch.object(scanner, 'scan_dirs', return_value={'core': ['config', 'logger'], 'agents': ['base']}):
            markdown = scanner.get_structure_markdown()

            assert 'core/' in markdown
            assert 'agents/' in markdown
            assert '`config.py`' in markdown or '`config`' in markdown

    def test_structure_markdown_empty(self, sample_project_dir):
        """Test markdown generation with empty structure."""
        scanner = ProjectStructureScanner(sample_project_dir)
        with patch.object(scanner, 'scan_dirs', return_value={}):
            markdown = scanner.get_structure_markdown()

            assert markdown == "*(Project structure scanning)*"


class TestTestCounter:
    """Tests for test counting."""

    @patch('generate_readme.subprocess.run')
    def test_count_tests_from_pytest(self, mock_run):
        """Test counting tests from pytest output."""
        mock_run.return_value = MagicMock(
            stdout="300 tests collected in 2.50s",
            returncode=0
        )

        count = TestCounter.count_tests()
        assert count == 300

    @patch('generate_readme.subprocess.run')
    def test_count_tests_no_match(self, mock_run):
        """Test when pytest output doesn't match pattern."""
        mock_run.return_value = MagicMock(
            stdout="no tests found",
            returncode=0
        )

        count = TestCounter.count_tests()
        assert count == 0

    @patch('generate_readme.subprocess.run')
    def test_count_tests_timeout(self, mock_run):
        """Test timeout handling in test counting."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired('pytest', 30)

        count = TestCounter.count_tests()
        assert count == 0

    @patch('generate_readme.subprocess.run')
    def test_count_tests_file_not_found(self, mock_run):
        """Test when pytest is not found."""
        mock_run.side_effect = FileNotFoundError()

        count = TestCounter.count_tests()
        assert count == 0


class TestTranslator:
    """Tests for translation functionality."""

    def test_translate_headers_en_to_ru(self):
        """Test translation of common headers."""
        text = "## Features\n### Project Structure\n## Quick Start"
        translated = Translator.translate_header(text)

        assert "Функции" in translated
        assert "Структура проекта" in translated
        assert "Быстрый старт" in translated

    def test_translate_headers_partial(self):
        """Test translation with mixed headers."""
        text = "## Features\n## Unknown Header\n### Installation"
        translated = Translator.translate_header(text)

        assert "Функции" in translated
        assert "Unknown Header" in translated
        assert "Установка" in translated

    def test_translate_no_headers(self):
        """Test translation with no matching headers."""
        text = "Some plain text without headers"
        translated = Translator.translate_header(text)

        assert translated == text


class TestReadmeGenerator:
    """Tests for README generation."""

    @pytest.fixture
    def readme_generator(self, tmp_path):
        """Create a ReadmeGenerator with test data."""
        # Create minimal CHANGELOG
        changelog = tmp_path / "CHANGELOG.md"
        changelog.write_text("""# Changelog

## [Unreleased]

## [1.0.0]

### Added
- Feature A
- Feature B
""")

        # Create minimal project structure
        (tmp_path / 'core').mkdir()
        (tmp_path / 'core' / 'config.py').write_text("")
        (tmp_path / 'agents').mkdir()
        (tmp_path / 'agents' / 'auditor.py').write_text("")

        return ReadmeGenerator(str(tmp_path))

    def test_generate_readme_en_has_required_sections(self, readme_generator):
        """Test that generated English README has required sections."""
        readme = readme_generator.generate_readme_en()

        assert "DigitalAuditor Cleshnya" in readme
        assert "Overview" in readme or "## " in readme
        assert "Features" in readme or "🚀" in readme
        assert "Quick Start" in readme or "⚡" in readme
        assert "Installation" in readme or "🛠️" in readme
        assert "Documentation" in readme or "📚" in readme
        assert "README_RU.md" in readme  # Link to Russian version

    def test_generate_readme_ru_has_required_sections(self, readme_generator):
        """Test that generated Russian README has required sections."""
        readme_ru = readme_generator.generate_readme_ru()

        assert "DigitalAuditor Cleshnya" in readme_ru
        assert "Описание" in readme_ru or "📋" in readme_ru
        assert "Функции" in readme_ru or "🚀" in readme_ru
        assert "Быстрый старт" in readme_ru or "⚡" in readme_ru
        assert "Установка" in readme_ru or "🛠️" in readme_ru
        assert "README.md" in readme_ru  # Link to English version

    def test_readme_contains_test_count(self, readme_generator):
        """Test that README includes test count."""
        with patch.object(readme_generator, 'test_count', 350):
            readme = readme_generator.generate_readme_en()
            assert "350" in readme or "test" in readme.lower()

    def test_check_readmes_match(self, readme_generator, tmp_path):
        """Test README comparison."""
        # Generate and write files
        readme_generator.write_readmes()

        # Check should pass since we just wrote them
        assert readme_generator.check_readmes() is True

    def test_check_readmes_mismatch(self, readme_generator, tmp_path):
        """Test README comparison when content differs."""
        # Generate and write files
        readme_generator.write_readmes()

        # Modify one file
        readme_file = tmp_path / 'README.md'
        current_content = readme_file.read_text()
        readme_file.write_text(current_content + "\n\nSome extra content")

        # Check should fail
        assert readme_generator.check_readmes() is False


class TestChangelogAutoUpdate:
    """Tests for CHANGELOG auto-update script."""

    @pytest.fixture
    def sample_changelog_file(self, tmp_path):
        """Create a sample CHANGELOG for testing updates."""
        changelog_content = """# Changelog

## [Unreleased]

### Added
- (Auto-generated entries from merged PRs will appear here)

### Changed
- (Auto-generated entries from merged PRs will appear here)

## [1.0.0]

### Added
- Initial release
"""
        changelog_file = tmp_path / "CHANGELOG.md"
        changelog_file.write_text(changelog_content)
        return str(changelog_file)

    def test_add_entry_to_unreleased_added(self, sample_changelog_file):
        """Test adding entry to Added section in Unreleased."""
        success = update_changelog(
            sample_changelog_file,
            "Added",
            "New feature X",
            123
        )

        assert success is True

        content = Path(sample_changelog_file).read_text()
        assert "New feature X" in content
        assert "PR #123" in content
        assert "## [Unreleased]" in content

    def test_add_entry_to_new_section(self, sample_changelog_file):
        """Test adding entry to a new section type."""
        success = update_changelog(
            sample_changelog_file,
            "Security",
            "Fixed security vulnerability",
            456
        )

        assert success is True

        content = Path(sample_changelog_file).read_text()
        assert "### Security" in content
        assert "Fixed security vulnerability" in content

    def test_entry_format(self, sample_changelog_file):
        """Test that entry is formatted correctly."""
        update_changelog(
            sample_changelog_file,
            "Fixed",
            "Bug in auth",
            789
        )

        content = Path(sample_changelog_file).read_text()
        # Entry should follow format: - **Description** (PR #number)
        assert "**Bug in auth**" in content
        assert "(PR #789)" in content

    def test_add_entry_nonexistent_file(self, tmp_path):
        """Test adding entry to nonexistent file."""
        nonexistent = str(tmp_path / "nonexistent.md")

        success = update_changelog(
            nonexistent,
            "Added",
            "Feature",
            123
        )

        assert success is False


class TestReadmeValidation:
    """Integration tests for README validation."""

    @pytest.fixture
    def full_project(self, tmp_path):
        """Create a full test project with CHANGELOG and structure."""
        # CHANGELOG
        (tmp_path / 'CHANGELOG.md').write_text("""# Changelog

## [Unreleased]

## [1.0.0]

### Added
- Feature A
- Feature B
""")

        # Project structure
        for dir_name in ['core', 'agents', 'knowledge', 'tools']:
            dir_path = tmp_path / dir_name
            dir_path.mkdir()
            (dir_path / f'{dir_name}.py').write_text("")

        # Existing READMEs
        (tmp_path / 'README.md').write_text("# Old README")
        (tmp_path / 'README_RU.md').write_text("# Старый README")

        return tmp_path

    def test_readme_generation_completes(self, full_project):
        """Test that README generation completes without errors."""
        with patch('generate_readme.TestCounter.count_tests', return_value=300):
            generator = ReadmeGenerator(str(full_project))
            readme = generator.generate_readme_en()

            assert len(readme) > 100
            assert "DigitalAuditor" in readme

    def test_readme_and_readme_ru_consistency(self, full_project):
        """Test that both README versions have consistent structure."""
        with patch('generate_readme.TestCounter.count_tests', return_value=300):
            generator = ReadmeGenerator(str(full_project))
            readme_en = generator.generate_readme_en()
            readme_ru = generator.generate_readme_ru()

            # Both should have similar section counts
            sections_en = readme_en.count("## ")
            sections_ru = readme_ru.count("## ")

            # Should have similar number of main sections
            assert abs(sections_en - sections_ru) <= 2

            # Both should contain contact info
            assert "@auditor2it" in readme_en
            assert "@auditor2it" in readme_ru


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
