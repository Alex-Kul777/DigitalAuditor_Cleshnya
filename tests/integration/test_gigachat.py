"""Integration tests for GigaChat LLM provider."""
import os
import pytest
from unittest.mock import patch, MagicMock
from core.gigachat_client import GigaChatClient
from core.llm import GigaChatWrapper, LLMFactory, get_llm


@pytest.mark.integration
class TestGigaChatClient:
    """Tests for GigaChatClient."""

    def test_gigachat_client_initialization_with_scope(self):
        """Test GigaChatClient initializes with scope parameter."""
        client = GigaChatClient(
            api_key="test_key",
            model="GigaChat-2-Max",
            scope="GIGACHAT_API_B2B"
        )
        assert client.api_key == "test_key"
        assert client.model == "GigaChat-2-Max"
        assert client.scope == "GIGACHAT_API_B2B"

    def test_gigachat_client_default_scope_from_env(self, monkeypatch):
        """Test GigaChatClient uses default scope from environment."""
        monkeypatch.setenv("GIGACHAT_SCOPE", "GIGACHAT_API_B2B")
        client = GigaChatClient(api_key="test_key")
        assert client.scope == "GIGACHAT_API_B2B"

    def test_gigachat_client_env_api_key(self, monkeypatch):
        """Test GigaChatClient reads API key from environment."""
        monkeypatch.setenv("GIGACHAT_API_KEY", "env_key")
        monkeypatch.setenv("GIGACHAT_MODEL", "GigaChat-2-Max")
        client = GigaChatClient()
        assert client.api_key == "env_key"
        assert client.model == "GigaChat-2-Max"

    def test_gigachat_client_circuit_breaker(self):
        """Test circuit breaker functionality."""
        client = GigaChatClient(api_key="test", max_retries=2)
        assert not client._circuit_open

        # Record failures
        client._record_failure()
        client._record_failure()
        assert client._circuit_open

    def test_gigachat_client_record_success(self):
        """Test success resets circuit breaker."""
        client = GigaChatClient(api_key="test", max_retries=2)
        client._record_failure()
        client._record_success()
        assert not client._circuit_open
        assert client._failure_count == 0


@pytest.mark.integration
class TestGigaChatWrapper:
    """Tests for GigaChatWrapper."""

    def test_gigachat_wrapper_initialization(self):
        """Test GigaChatWrapper initializes with scope."""
        wrapper = GigaChatWrapper(
            api_key="test_key",
            model="GigaChat-2-Max",
            scope="GIGACHAT_API_B2B",
            temperature=0.3
        )
        assert wrapper.client.scope == "GIGACHAT_API_B2B"
        assert wrapper.temperature == 0.3
        assert wrapper.client.model == "GigaChat-2-Max"

    def test_gigachat_wrapper_default_scope(self):
        """Test GigaChatWrapper uses default scope."""
        wrapper = GigaChatWrapper(
            api_key="test_key",
            model="GigaChat-2-Max"
        )
        assert wrapper.client.scope == "GIGACHAT_API_B2B"


@pytest.mark.integration
class TestLLMFactory:
    """Tests for LLM Factory provider selection."""

    def test_llm_factory_ollama_provider(self, monkeypatch):
        """Test LLM Factory returns OllamaLLM."""
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        llm = LLMFactory.get_llm(temperature=0.3)
        assert llm.__class__.__name__ == "OllamaLLM"

    def test_llm_factory_gigachat_provider(self, monkeypatch):
        """Test LLM Factory returns GigaChatLLMAdapter for gigachat."""
        monkeypatch.setenv("LLM_PROVIDER", "gigachat")
        monkeypatch.setenv("GIGACHAT_API_KEY", "test_key")
        llm = LLMFactory.get_llm(temperature=0.3)
        assert llm.__class__.__name__ == "GigaChatLLMAdapter"
        assert llm.temperature == 0.3

    def test_llm_factory_hybrid_mode_fallback(self, monkeypatch):
        """Test hybrid mode falls back to Ollama when GigaChat unavailable."""
        monkeypatch.setenv("LLM_PROVIDER", "hybrid")
        monkeypatch.delenv("GIGACHAT_API_KEY", raising=False)
        llm = LLMFactory.get_llm(temperature=0.3)
        assert llm.__class__.__name__ == "OllamaLLM"

    def test_get_llm_function(self, monkeypatch):
        """Test backward-compatible get_llm() function."""
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        llm = get_llm(temperature=0.3)
        assert llm.__class__.__name__ == "OllamaLLM"


@pytest.mark.integration
class TestGigaChatIntegration:
    """Integration tests with actual GigaChat API (if available)."""

    @pytest.mark.skipif(
        not os.getenv("GIGACHAT_API_KEY"),
        reason="GIGACHAT_API_KEY not set"
    )
    def test_gigachat_client_invoke(self):
        """Test GigaChatClient invoke with real API."""
        client = GigaChatClient(
            api_key=os.getenv("GIGACHAT_API_KEY"),
            scope="GIGACHAT_API_B2B"
        )
        response = client.invoke("Привет мир")
        assert response is not None
        assert isinstance(response, str)

    @pytest.mark.skipif(
        not os.getenv("GIGACHAT_API_KEY"),
        reason="GIGACHAT_API_KEY not set"
    )
    def test_gigachat_wrapper_invoke(self):
        """Test GigaChatWrapper invoke with real API."""
        wrapper = GigaChatWrapper(
            api_key=os.getenv("GIGACHAT_API_KEY"),
            model="GigaChat-2-Max",
            scope="GIGACHAT_API_B2B"
        )
        response = wrapper.invoke("Привет")
        assert response is not None
        assert isinstance(response, str)


@pytest.mark.unit
class TestGigaChatConfig:
    """Tests for GigaChat configuration."""

    def test_gigachat_scope_in_config(self, monkeypatch):
        """Test GIGACHAT_SCOPE available in config."""
        from core.config import GIGACHAT_SCOPE
        assert GIGACHAT_SCOPE == "GIGACHAT_API_B2B"

    def test_gigachat_config_vars(self, monkeypatch):
        """Test all GigaChat config variables."""
        from core.config import (
            GIGACHAT_API_KEY,
            GIGACHAT_SCOPE,
            GIGACHAT_MODEL,
            GIGACHAT_MAX_TOKENS,
            GIGACHAT_TIMEOUT,
            GIGACHAT_MAX_RETRIES
        )
        assert isinstance(GIGACHAT_SCOPE, str)
        assert isinstance(GIGACHAT_MODEL, str)
        assert isinstance(GIGACHAT_MAX_TOKENS, int)
        assert isinstance(GIGACHAT_TIMEOUT, int)
        assert isinstance(GIGACHAT_MAX_RETRIES, int)
