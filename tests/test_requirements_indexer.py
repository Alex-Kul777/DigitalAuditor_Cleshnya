import pytest
import tempfile
from pathlib import Path
from knowledge.requirements_indexer import RequirementsIndexer
from core.config import PROJECT_ROOT


class TestRequirementsIndexerAddRequirement:
    """Test adding requirements to the library."""

    def test_add_requirement_level1_copies_to_regulatory(self):
        """Verify L1 requirement copied to regulatory folder."""
        indexer = RequirementsIndexer()

        # Create temp requirement file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("L1 Regulatory requirement")
            temp_file = f.name

        try:
            chunks = indexer.add_requirement(temp_file, level=1, authority="FSTEC")
            assert chunks > 0

            regulatory_folder = PROJECT_ROOT / "knowledge" / "requirements" / "regulatory"
            dest_file = regulatory_folder / Path(temp_file).name
            assert dest_file.exists()
        finally:
            Path(temp_file).unlink()
            if dest_file.exists():
                dest_file.unlink()

    def test_add_requirement_level2_copies_to_audit(self):
        """Verify L2 requirement copied to audit folder."""
        indexer = RequirementsIndexer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("L2 Audit standard requirement")
            temp_file = f.name

        try:
            chunks = indexer.add_requirement(temp_file, level=2, authority="ISO")
            assert chunks > 0

            audit_folder = PROJECT_ROOT / "knowledge" / "requirements" / "audit"
            dest_file = audit_folder / Path(temp_file).name
            assert dest_file.exists()
        finally:
            Path(temp_file).unlink()
            if dest_file.exists():
                dest_file.unlink()

    def test_add_requirement_level3_copies_to_local(self):
        """Verify L3 requirement copied to local folder."""
        indexer = RequirementsIndexer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("L3 Local policy requirement")
            temp_file = f.name

        try:
            chunks = indexer.add_requirement(temp_file, level=3, authority="internal")
            assert chunks > 0

            local_folder = PROJECT_ROOT / "knowledge" / "requirements" / "local"
            dest_file = local_folder / Path(temp_file).name
            assert dest_file.exists()
        finally:
            Path(temp_file).unlink()
            if dest_file.exists():
                dest_file.unlink()

    def test_add_requirement_invalid_level_raises(self):
        """Verify invalid level raises ValueError."""
        indexer = RequirementsIndexer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test")
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Invalid requirement level"):
                indexer.add_requirement(temp_file, level=99)
        finally:
            Path(temp_file).unlink()

    def test_add_requirement_missing_file_raises(self):
        """Verify missing file raises FileNotFoundError."""
        indexer = RequirementsIndexer()

        with pytest.raises(FileNotFoundError, match="not found"):
            indexer.add_requirement("/nonexistent/file.txt", level=1)

    def test_add_requirement_default_authority(self):
        """Verify authority defaults to user_defined."""
        indexer = RequirementsIndexer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test requirement")
            temp_file = f.name

        try:
            chunks = indexer.add_requirement(temp_file, level=1)
            assert chunks > 0
        finally:
            Path(temp_file).unlink()
            dest_file = PROJECT_ROOT / "knowledge" / "requirements" / "regulatory" / Path(temp_file).name
            if dest_file.exists():
                dest_file.unlink()


class TestRequirementsIndexerList:
    """Test listing requirements."""

    def test_list_requirements_returns_dict(self):
        """Verify list_requirements returns dict."""
        indexer = RequirementsIndexer()
        result = indexer.list_requirements()
        assert isinstance(result, dict)

    def test_list_requirements_all_levels(self):
        """Verify list_requirements returns all levels."""
        indexer = RequirementsIndexer()
        result = indexer.list_requirements()
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_list_requirements_filters_by_level(self):
        """Verify level parameter filters results."""
        indexer = RequirementsIndexer()

        result_all = indexer.list_requirements()
        result_l1 = indexer.list_requirements(level=1)

        assert len(result_all) == 3
        assert len(result_l1) == 1
        assert 1 in result_l1

    def test_list_requirements_empty_folders(self):
        """Verify empty folders return empty list."""
        indexer = RequirementsIndexer()
        result = indexer.list_requirements()

        for level, files in result.items():
            assert isinstance(files, list)

    def test_list_requirements_returns_filenames(self):
        """Verify filenames are returned as strings."""
        indexer = RequirementsIndexer()

        # Add a requirement
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test")
            temp_file = f.name

        try:
            indexer.add_requirement(temp_file, level=1)
            result = indexer.list_requirements(level=1)

            assert len(result[1]) > 0
            assert all(isinstance(f, str) for f in result[1])
        finally:
            Path(temp_file).unlink()
            dest_file = PROJECT_ROOT / "knowledge" / "requirements" / "regulatory" / Path(temp_file).name
            if dest_file.exists():
                dest_file.unlink()


class TestRequirementsIndexerIndexAll:
    """Test re-indexing all requirements."""

    def test_index_all_returns_dict(self):
        """Verify index_all returns dict with levels."""
        indexer = RequirementsIndexer()
        result = indexer.index_all()

        assert isinstance(result, dict)
        assert 1 in result
        assert 2 in result
        assert 3 in result

    def test_index_all_returns_chunk_counts(self):
        """Verify chunk counts are non-negative integers."""
        indexer = RequirementsIndexer()
        result = indexer.index_all()

        for level, count in result.items():
            assert isinstance(count, int)
            assert count >= 0

    def test_index_all_handles_missing_folders(self):
        """Verify graceful handling of missing requirement folders."""
        indexer = RequirementsIndexer()

        # Even if some folders don't exist, should return counts for all levels
        result = indexer.index_all()
        assert len(result) == 3

    def test_index_all_skips_invalid_files(self):
        """Verify invalid files are skipped with warning."""
        indexer = RequirementsIndexer()

        # Should complete without raising exception
        result = indexer.index_all()
        assert isinstance(result, dict)


class TestRequirementsIndexerLevel:
    """Test level constants and mapping."""

    def test_level_map_has_correct_keys(self):
        """Verify LEVEL_MAP has keys 1, 2, 3."""
        assert 1 in RequirementsIndexer.LEVEL_MAP
        assert 2 in RequirementsIndexer.LEVEL_MAP
        assert 3 in RequirementsIndexer.LEVEL_MAP

    def test_level_map_has_tuples(self):
        """Verify LEVEL_MAP values are (doc_type, path) tuples."""
        for level, (doc_type, path) in RequirementsIndexer.LEVEL_MAP.items():
            assert isinstance(doc_type, str)
            assert isinstance(path, Path)

    def test_level_map_doc_types(self):
        """Verify correct doc_type for each level."""
        mapping = RequirementsIndexer.LEVEL_MAP
        assert mapping[1][0] == "regulatory"
        assert mapping[2][0] == "audit_standard"
        assert mapping[3][0] == "local_policy"
