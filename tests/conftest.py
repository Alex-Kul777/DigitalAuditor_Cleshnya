"""
Pytest fixtures and configuration for DigitalAuditor tests.
"""
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
import tempfile
import pytest
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def sample_audit_config():
    """Sample audit configuration for testing."""
    return {
        "name": "test_audit",
        "company": "Test Company",
        "audit_type": "it",
        "sources": ["test_source"],
        "created": "2026-04-20T12:00:00",
    }


@pytest.fixture
def tmp_task_dir(tmp_path):
    """Create temporary task directory with standard structure."""
    task_dir = tmp_path / "test_task"
    task_dir.mkdir()

    # Create standard subdirectories
    (task_dir / "evidence").mkdir()
    (task_dir / "drafts").mkdir()
    (task_dir / "output").mkdir()

    # Create gitkeep files
    (task_dir / "evidence" / ".gitkeep").touch()
    (task_dir / "drafts" / ".gitkeep").touch()

    # Create sample config.yaml
    config = {
        "name": "test_task",
        "company": "Test Corp",
        "audit_type": "it",
        "sources": [],
        "created": "2026-04-20T12:00:00",
    }
    config_path = task_dir / "config.yaml"
    config_path.write_text(yaml.dump(config))

    return task_dir


@pytest.fixture
def env_testing(monkeypatch, tmp_path):
    """Set up testing environment variables."""
    monkeypatch.setenv("AUDIT_PROFILE", "testing")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CHROMA_DB_PATH", str(tmp_path / "chroma_db"))
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "digital-auditor-cisa")


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_ollama_llm():
    """Mock Ollama LLM instance."""
    mock_llm = MagicMock()
    mock_llm.invoke = MagicMock(
        return_value="Test response from Ollama"
    )
    mock_llm.predict = MagicMock(
        return_value="Test prediction"
    )
    return mock_llm


@pytest.fixture
def mock_chroma_db():
    """Mock ChromaDB vector store."""
    mock_db = MagicMock()
    mock_db.add = MagicMock(return_value=["doc_id_1"])
    mock_db.query = MagicMock(
        return_value={
            "ids": [["doc_id_1"]],
            "documents": [["Test document content"]],
            "metadatas": [[{"source": "test"}]],
            "distances": [[0.1]],
        }
    )
    mock_db.get = MagicMock(
        return_value={
            "ids": ["doc_id_1"],
            "documents": ["Test document"],
            "metadatas": [{"source": "test"}],
        }
    )
    return mock_db


@pytest.fixture
def mock_embedder():
    """Mock sentence-transformers embedder."""
    mock_embed = MagicMock()
    mock_embed.encode = MagicMock(
        return_value=[[0.1, 0.2, 0.3]]
    )
    return mock_embed


# ============================================================================
# Markers and Test Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )
