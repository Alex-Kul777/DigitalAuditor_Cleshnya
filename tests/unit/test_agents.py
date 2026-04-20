"""
Unit tests for agents module.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from agents.base import BaseAgent
from agents.cisa_auditor import CisaAuditor, SYSTEM_PROMPT


class TestBaseAgent:
    """Test BaseAgent abstract base class."""

    def test_base_agent_cannot_be_instantiated(self):
        """Test that BaseAgent cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseAgent("test_agent")

    def test_base_agent_subclass_requires_execute(self):
        """Test that BaseAgent subclass must implement execute."""
        class IncompleteAgent(BaseAgent):
            pass

        with pytest.raises(TypeError):
            IncompleteAgent("incomplete")

    def test_base_agent_subclass_with_execute(self):
        """Test that BaseAgent subclass with execute() works."""
        class SimpleAgent(BaseAgent):
            def execute(self, task: str) -> str:
                return f"Executed: {task}"

        with patch("agents.base.get_llm") as mock_get_llm:
            with patch("agents.base.setup_logger"):
                agent = SimpleAgent("simple")
                result = agent.execute("test_task")
                assert result == "Executed: test_task"

    def test_base_agent_initialization(self):
        """Test BaseAgent initialization with mocked dependencies."""
        class TestAgent(BaseAgent):
            def execute(self, task: str) -> str:
                return "test"

        with patch("agents.base.get_llm") as mock_get_llm:
            with patch("agents.base.setup_logger") as mock_logger:
                agent = TestAgent("test_agent")
                assert agent.name == "test_agent"
                mock_get_llm.assert_called_once()
                mock_logger.assert_called_once_with("agent.test_agent")


class TestCisaAuditor:
    """Test CisaAuditor agent."""

    def test_cisa_auditor_initialization(self, mock_ollama_llm):
        """Test CisaAuditor initialization."""
        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()
                assert auditor.name == "cisa_auditor"
                assert auditor.llm is not None

    def test_cisa_auditor_execute(self, mock_ollama_llm):
        """Test CisaAuditor.execute() method."""
        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()
                result = auditor.execute("проверить ИТ-безопасность")

                # Verify invoke was called with prompt containing system prompt and task
                mock_ollama_llm.invoke.assert_called_once()
                called_prompt = mock_ollama_llm.invoke.call_args[0][0]
                assert SYSTEM_PROMPT in called_prompt
                assert "проверить ИТ-безопасность" in called_prompt

    def test_cisa_auditor_generate_section(self, mock_ollama_llm):
        """Test CisaAuditor.generate_section() method."""
        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()
                result = auditor.generate_section("Опишите архитектуру безопасности")

                # Verify invoke was called with system prompt and section prompt
                mock_ollama_llm.invoke.assert_called_once()
                called_prompt = mock_ollama_llm.invoke.call_args[0][0]
                assert SYSTEM_PROMPT in called_prompt
                assert "Опишите архитектуру безопасности" in called_prompt

    def test_cisa_auditor_uses_correct_model(self):
        """Test that CisaAuditor uses correct model and temperature."""
        with patch("agents.cisa_auditor.OllamaLLM") as mock_ollama_class:
            with patch("agents.base.setup_logger"):
                with patch("agents.cisa_auditor.OLLAMA_BASE_URL", "http://localhost:11434"):
                    with patch("agents.cisa_auditor.OLLAMA_MODEL", "digital-auditor-cisa"):
                        auditor = CisaAuditor()

                        # Verify OllamaLLM was called with correct parameters
                        mock_ollama_class.assert_called_once()
                        call_kwargs = mock_ollama_class.call_args[1]
                        assert call_kwargs["base_url"] == "http://localhost:11434"
                        assert call_kwargs["model"] == "digital-auditor-cisa"
                        assert call_kwargs["temperature"] == 0.3
                        assert call_kwargs["num_ctx"] == 8192

    def test_cisa_auditor_system_prompt_is_russian(self):
        """Test that CISA auditor uses Russian system prompt."""
        assert "CISA" in SYSTEM_PROMPT
        assert "CIA" in SYSTEM_PROMPT
        assert "ИТ-аудитор" in SYSTEM_PROMPT
        assert "русском языке" in SYSTEM_PROMPT or "русском" in SYSTEM_PROMPT

    def test_cisa_auditor_multiple_executions(self, mock_ollama_llm):
        """Test multiple executions with different tasks."""
        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()

                task1 = "проверить доступы"
                task2 = "проверить логирование"

                auditor.execute(task1)
                auditor.execute(task2)

                # Verify invoke was called twice
                assert mock_ollama_llm.invoke.call_count == 2

                # Verify both tasks were included in calls
                calls = [call[0][0] for call in mock_ollama_llm.invoke.call_args_list]
                assert any(task1 in call for call in calls)
                assert any(task2 in call for call in calls)


class TestAgentLLMInteraction:
    """Test agent interaction with LLM."""

    def test_agent_calls_llm_invoke(self, mock_ollama_llm):
        """Test that agent calls llm.invoke() method."""
        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()
                auditor.execute("test task")

                # Verify that invoke was called
                mock_ollama_llm.invoke.assert_called_once()

    def test_agent_returns_llm_response(self, mock_ollama_llm):
        """Test that agent returns LLM response."""
        expected_response = "Test audit findings"
        mock_ollama_llm.invoke.return_value = expected_response

        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()
                result = auditor.execute("test task")

                assert result == expected_response

    def test_agent_handles_empty_response(self, mock_ollama_llm):
        """Test agent handles empty LLM response."""
        mock_ollama_llm.invoke.return_value = ""

        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()
                result = auditor.execute("test task")

                assert result == ""

    def test_agent_handles_long_response(self, mock_ollama_llm):
        """Test agent handles long LLM response."""
        long_response = "A" * 10000
        mock_ollama_llm.invoke.return_value = long_response

        with patch("agents.cisa_auditor.OllamaLLM", return_value=mock_ollama_llm):
            with patch("agents.base.setup_logger"):
                auditor = CisaAuditor()
                result = auditor.execute("test task")

                assert result == long_response
                assert len(result) == 10000


@pytest.mark.unit
class TestAgentMarker:
    """Test agents module with unit marker."""

    def test_base_agent_exists(self):
        """Test that BaseAgent class exists."""
        assert BaseAgent is not None

    def test_cisa_auditor_exists(self):
        """Test that CisaAuditor class exists."""
        assert CisaAuditor is not None

    def test_system_prompt_is_defined(self):
        """Test that SYSTEM_PROMPT is defined."""
        assert SYSTEM_PROMPT is not None
        assert isinstance(SYSTEM_PROMPT, str)
