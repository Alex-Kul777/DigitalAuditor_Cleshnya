from pathlib import Path
import yaml
from core.logger import setup_logger
from core.validator import InputValidator
from core.exceptions import (
    AuditError,
    ConfigurationError,
    OllamaUnavailableError,
)
from knowledge.fetcher import DocumentFetcher
from knowledge.indexer import VectorIndexer
from report_generator.orchestrator import ReportOrchestrator


class AuditTask:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.logger = setup_logger(f"task.{task_dir.name}")
        self.config = self._load_config()
        self.fetcher = DocumentFetcher()
        self.indexer = VectorIndexer()
        self.orchestrator = ReportOrchestrator(task_dir)

    def _load_config(self) -> dict:
        config_path = self.task_dir / "config.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return {}

    def execute(self):
        task_name = self.config.get('name', 'unknown')
        try:
            self.logger.info(f"Executing task: {task_name}")

            # Validate configuration before proceeding
            validation = InputValidator.validate_task_config(self.config)
            if not validation.is_valid:
                error_msg = f"Task configuration invalid: {len(validation.errors)} error(s)"
                self.logger.error(error_msg)
                for error in validation.errors:
                    self.logger.error(
                        f"  [{error.error_code}] {error.field}: {error.message}"
                    )
                raise ConfigurationError(error_msg, missing_fields=[e.field for e in validation.errors])

            # Log warnings
            for warning in validation.warnings:
                self.logger.warning(f"Configuration warning: {warning}")

            # Execute audit workflow
            findings = []
            self.orchestrator.generate(findings)
            self.logger.info("Task completed successfully")

        except AuditError as e:
            self.logger.error(f"Audit error in task '{task_name}': {str(e)}")
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error in task '{task_name}': {str(e)}",
                exc_info=True
            )
            raise AuditError(
                f"Task execution failed: {str(e)}",
                error_code="TASK_EXECUTION_FAILED"
            ) from e
