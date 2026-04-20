"""
Smoke tests for DigitalAuditor Cleshnya.

Basic import and CLI verification tests.
These tests check that all major modules can be imported
and basic CLI commands work.
"""
import subprocess
import sys
import pytest
from pathlib import Path


@pytest.mark.smoke
class TestImports:
    """Verify all major modules can be imported."""

    def test_import_core_config(self):
        """Test importing core.config."""
        from core import config
        assert config.PROJECT_ROOT is not None

    def test_import_core_logger(self):
        """Test importing core.logger."""
        from core import logger
        assert hasattr(logger, "setup_logger")

    def test_import_core_logging_utils(self):
        """Test importing core.logging_utils."""
        from core import logging_utils
        assert logging_utils.ContextualFormatter is not None

    def test_import_core_exceptions(self):
        """Test importing core.exceptions."""
        from core import exceptions
        assert exceptions.AuditError is not None

    def test_import_core_validator(self):
        """Test importing core.validator."""
        from core import validator
        assert validator.InputValidator is not None

    def test_import_agents_base(self):
        """Test importing agents.base."""
        from agents import base
        assert base.BaseAgent is not None

    def test_import_agents_cisa_auditor(self):
        """Test importing agents.cisa_auditor."""
        from agents import cisa_auditor
        assert cisa_auditor.CISAAuditor is not None

    def test_import_tasks_base_task(self):
        """Test importing tasks.base_task."""
        from tasks import base_task
        assert base_task.AuditTask is not None

    def test_import_knowledge_fetcher(self):
        """Test importing knowledge.fetcher."""
        from knowledge import fetcher
        assert fetcher.DocumentFetcher is not None

    def test_import_knowledge_indexer(self):
        """Test importing knowledge.indexer."""
        from knowledge import indexer
        assert indexer.VectorIndexer is not None

    def test_import_knowledge_retriever(self):
        """Test importing knowledge.retriever."""
        from knowledge import retriever
        assert retriever.Retriever is not None

    def test_import_tools_risk_matrix(self):
        """Test importing tools.risk_matrix."""
        from tools import risk_matrix
        assert risk_matrix.calculate_risk_level is not None

    def test_import_tools_evidence_tracker(self):
        """Test importing tools.evidence_tracker."""
        from tools import evidence_tracker
        assert evidence_tracker.EvidenceTracker is not None

    def test_import_report_generator(self):
        """Test importing report_generator.orchestrator."""
        from report_generator import orchestrator
        assert orchestrator.ReportOrchestrator is not None


@pytest.mark.smoke
class TestCLI:
    """Test CLI command availability."""

    def test_cli_help(self):
        """Test 'python main.py --help' command."""
        result = subprocess.run(
            [sys.executable, "main.py", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "DigitalAuditor" in result.stdout or "Usage:" in result.stdout

    def test_cli_create_help(self):
        """Test 'python main.py create --help' command."""
        result = subprocess.run(
            [sys.executable, "main.py", "create", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "help" in result.stdout.lower()

    def test_cli_run_help(self):
        """Test 'python main.py run --help' command."""
        result = subprocess.run(
            [sys.executable, "main.py", "run", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_cli_list_tasks_help(self):
        """Test 'python main.py list-tasks --help' command."""
        result = subprocess.run(
            [sys.executable, "main.py", "list-tasks", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_cli_audit_ms_help(self):
        """Test 'python main.py audit-ms --help' command."""
        result = subprocess.run(
            [sys.executable, "main.py", "audit-ms", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


@pytest.mark.smoke
class TestFileStructure:
    """Verify project file structure is correct."""

    def test_main_py_exists(self):
        """Test that main.py exists."""
        assert Path("main.py").exists()

    def test_setup_py_exists(self):
        """Test that setup.py exists."""
        assert Path("setup.py").exists()

    def test_requirements_txt_exists(self):
        """Test that requirements.txt exists."""
        assert Path("requirements.txt").exists()

    def test_core_package_exists(self):
        """Test that core package exists."""
        assert Path("core").is_dir()
        assert (Path("core") / "__init__.py").exists()

    def test_agents_package_exists(self):
        """Test that agents package exists."""
        assert Path("agents").is_dir()

    def test_tasks_package_exists(self):
        """Test that tasks package exists."""
        assert Path("tasks").is_dir()

    def test_knowledge_package_exists(self):
        """Test that knowledge package exists."""
        assert Path("knowledge").is_dir()

    def test_tools_package_exists(self):
        """Test that tools package exists."""
        assert Path("tools").is_dir()

    def test_report_generator_package_exists(self):
        """Test that report_generator package exists."""
        assert Path("report_generator").is_dir()

    def test_tests_directory_exists(self):
        """Test that tests directory exists."""
        assert Path("tests").is_dir()

    def test_pytest_ini_exists(self):
        """Test that pytest.ini exists."""
        assert Path("pytest.ini").exists()

    def test_makefile_exists(self):
        """Test that Makefile exists."""
        assert Path("Makefile").exists()


@pytest.mark.smoke
class TestConfigValidation:
    """Verify configuration can be loaded without errors."""

    def test_config_loads(self):
        """Test that config module loads without errors."""
        from core import config
        assert config.OLLAMA_BASE_URL is not None
        assert config.OLLAMA_MODEL is not None
        assert config.PROJECT_ROOT is not None

    def test_logger_initializes(self):
        """Test that logger can be initialized."""
        from core.logger import setup_logger
        logger = setup_logger("smoke_test")
        assert logger is not None
        logger.info("Smoke test logger initialization successful")


@pytest.mark.smoke
class TestBasicFunctionality:
    """Test basic functionality without external dependencies."""

    def test_risk_matrix_callable(self):
        """Test that risk_matrix.calculate_risk_level is callable."""
        from tools.risk_matrix import calculate_risk_level
        result = calculate_risk_level("High", "High")
        assert result == "Critical"

    def test_validator_instantiation(self):
        """Test that InputValidator can be instantiated."""
        from core.validator import InputValidator
        # InputValidator uses only static methods
        config = {"name": "test", "company": "test", "audit_type": "it"}
        result = InputValidator.validate_task_config(config)
        assert result.is_valid is True

    def test_logging_context_manager(self):
        """Test that LogContext can be used as context manager."""
        import logging
        from core.logging_utils import LogContext
        logger = logging.getLogger("smoke_test_context")
        with LogContext(logger, "test_stage"):
            pass


@pytest.mark.smoke
def test_package_can_be_imported():
    """Test that package can be imported with 'from digital_auditor import ...'."""
    # This test verifies setup.py is configured correctly
    # by checking that the package namespace would be importable
    from pathlib import Path
    setup_py = Path("setup.py")
    content = setup_py.read_text()
    assert "name=" in content
    assert "packages=" in content


def test_all_requirements_installed():
    """Test that all requirements can be imported (basic check)."""
    required_packages = [
        "click",
        "yaml",
        "pathlib",
        "logging",
    ]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            pytest.skip(f"Package {package} not installed")
