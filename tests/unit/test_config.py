"""
Unit tests for core.config module.
"""
import os
import sys
import importlib
from pathlib import Path
import pytest
from unittest.mock import patch

# Import the module to test
from core import config


class TestConfigDefaults:
    """Test configuration default values."""

    def test_ollama_base_url_default(self):
        """Test OLLAMA_BASE_URL default value."""
        # This might be overridden by env, but we check the fallback
        assert config.OLLAMA_BASE_URL is not None
        assert isinstance(config.OLLAMA_BASE_URL, str)
        assert config.OLLAMA_BASE_URL.startswith("http")

    def test_ollama_model_default(self):
        """Test OLLAMA_MODEL default value."""
        assert config.OLLAMA_MODEL is not None
        assert isinstance(config.OLLAMA_MODEL, str)
        assert "digital-auditor" in config.OLLAMA_MODEL.lower()

    def test_log_level_default(self):
        """Test LOG_LEVEL default value."""
        assert config.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def test_project_root(self):
        """Test PROJECT_ROOT is properly set."""
        assert config.PROJECT_ROOT.exists()
        assert config.PROJECT_ROOT.is_dir()
        assert (config.PROJECT_ROOT / "core").exists()

    def test_knowledge_raw_docs_path(self):
        """Test KNOWLEDGE_RAW_DOCS path is relative to PROJECT_ROOT."""
        assert config.KNOWLEDGE_RAW_DOCS == config.PROJECT_ROOT / "knowledge" / "raw_docs"

    def test_chroma_db_path(self):
        """Test CHROMA_DB_PATH is relative to PROJECT_ROOT."""
        assert config.CHROMA_DB_PATH == config.PROJECT_ROOT / "chroma_db"

    def test_embedding_model(self):
        """Test EMBEDDING_MODEL is properly set."""
        assert config.EMBEDDING_MODEL == "paraphrase-multilingual-MiniLM-L12-v2"


class TestConfigEnvironmentOverride:
    """Test that environment variables override defaults."""

    def test_ollama_base_url_override(self, monkeypatch):
        """Test OLLAMA_BASE_URL can be overridden via env."""
        test_url = "http://custom-ollama:11434"
        monkeypatch.setenv("OLLAMA_BASE_URL", test_url)
        # Re-import to get the new value
        import importlib
        importlib.reload(config)
        assert config.OLLAMA_BASE_URL == test_url

    def test_ollama_model_override(self, monkeypatch):
        """Test OLLAMA_MODEL can be overridden via env."""
        test_model = "custom-model"
        monkeypatch.setenv("OLLAMA_MODEL", test_model)
        importlib.reload(config)
        assert config.OLLAMA_MODEL == test_model

    def test_log_level_override(self, monkeypatch):
        """Test LOG_LEVEL can be overridden via env."""
        test_level = "DEBUG"
        monkeypatch.setenv("LOG_LEVEL", test_level)
        importlib.reload(config)
        assert config.LOG_LEVEL == test_level

    def test_log_file_override(self, monkeypatch):
        """Test LOG_FILE can be overridden via env."""
        test_file = "custom_audit.log"
        monkeypatch.setenv("LOG_FILE", test_file)
        importlib.reload(config)
        assert config.LOG_FILE == test_file


class TestConfigPaths:
    """Test path-related configuration."""

    def test_log_file_path(self):
        """Test LOG_FILE is a string path."""
        assert isinstance(config.LOG_FILE, str)
        assert config.LOG_FILE.endswith(".log")

    def test_paths_are_pathlib(self):
        """Test that path configs are Path objects."""
        assert isinstance(config.PROJECT_ROOT, Path)
        assert isinstance(config.KNOWLEDGE_RAW_DOCS, Path)
        assert isinstance(config.CHROMA_DB_PATH, Path)


@pytest.mark.unit
class TestConfigIntegration:
    """Integration tests for config module."""

    def test_config_module_loads_without_error(self):
        """Test that config module loads without raising exceptions."""
        # If we got here, config loaded successfully
        assert config.PROJECT_ROOT is not None

    def test_tavily_api_key_exists(self):
        """Test TAVILY_API_KEY is defined (may be empty)."""
        assert hasattr(config, "TAVILY_API_KEY")
        assert isinstance(config.TAVILY_API_KEY, str)
