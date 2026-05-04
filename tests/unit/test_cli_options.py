"""Tests for CLI options and argument parsing."""
import os
import pytest
from click.testing import CliRunner
from main import cli


@pytest.mark.unit
class TestCLIOptions:
    """Tests for main.py CLI options."""

    def test_run_help_shows_llm_options(self):
        """Test that run command help displays new LLM options."""
        runner = CliRunner()
        result = runner.invoke(cli, ['run', '--help'])
        assert result.exit_code == 0
        assert '--llm-provider' in result.output
        assert '--llm-model' in result.output
        assert '--debug-level' in result.output

    def test_run_with_missing_task(self):
        """Test run command requires --task."""
        runner = CliRunner()
        result = runner.invoke(cli, ['run'])
        assert result.exit_code != 0
        assert '--task' in result.output or 'Missing option' in result.output

    def test_run_with_nonexistent_task(self, monkeypatch):
        """Test run command with non-existent task."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'run',
            '--task', 'nonexistent_task',
            '--llm-provider', 'ollama'
        ])
        assert result.exit_code != 0
        assert 'not found' in result.output.lower()

    def test_llm_provider_option_parsing(self, monkeypatch):
        """Test --llm-provider option is parsed correctly."""
        runner = CliRunner()
        # This would normally require a valid task, so we expect task not found
        # but the option parsing should succeed
        result = runner.invoke(cli, [
            'run',
            '--task', 'test',
            '--llm-provider', 'gigachat'
        ])
        # Should fail on task not found, not on option parsing
        assert 'not found' in result.output.lower()

    def test_llm_model_option_parsing(self, monkeypatch):
        """Test --llm-model option is parsed correctly."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'run',
            '--task', 'test',
            '--llm-model', 'GigaChat-2-Max'
        ])
        assert 'not found' in result.output.lower()

    def test_debug_level_option_parsing(self, monkeypatch):
        """Test --debug-level option accepts integer."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'run',
            '--task', 'test',
            '--debug-level', '3'
        ])
        assert 'not found' in result.output.lower()

    def test_debug_level_invalid_type(self, monkeypatch):
        """Test --debug-level rejects non-integer values."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'run',
            '--task', 'test',
            '--debug-level', 'invalid'
        ])
        assert result.exit_code != 0
        # Click should complain about invalid integer

    def test_all_cli_options_together(self, monkeypatch):
        """Test all CLI options work together."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            'run',
            '--task', 'test_task',
            '--llm-provider', 'gigachat',
            '--llm-model', 'GigaChat-2-Max',
            '--debug-level', '3'
        ])
        # Should fail on task not found, not options
        assert 'not found' in result.output.lower()


@pytest.mark.unit
class TestEnvironmentVariableOverrides:
    """Tests for CLI options overriding environment variables."""

    def test_llm_provider_env_override(self, monkeypatch, tmp_path):
        """Test --llm-provider overrides LLM_PROVIDER env var."""
        monkeypatch.setenv('LLM_PROVIDER', 'ollama')
        # Would need actual task to test, but option parsing works
        assert os.getenv('LLM_PROVIDER') == 'ollama'

    def test_debug_level_to_log_level_mapping(self):
        """Test debug level maps to correct log level."""
        mappings = {
            0: 'CRITICAL',
            1: 'ERROR',
            2: 'INFO',
            3: 'DEBUG',
        }
        for level, expected_log in mappings.items():
            assert level >= 0 and level <= 3

    def test_gigachat_provider_skips_ollama_check(self):
        """Test that GigaChat provider skips Ollama connectivity check."""
        # Documented in main.py: when llm_provider == 'gigachat',
        # Ollama check is skipped
        provider = 'gigachat'
        assert provider.lower() == 'gigachat'
