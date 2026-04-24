from pathlib import Path
from datetime import datetime
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
from process_mining.process_mining_logger import ProcessMiningLogger


class AuditTask:
    def __init__(self, task_dir: Path):
        self.task_dir = task_dir
        self.logger = setup_logger(f"task.{task_dir.name}")
        self.config = self._load_config()
        self.fetcher = DocumentFetcher()
        self.indexer = VectorIndexer()
        self.orchestrator = ReportOrchestrator(task_dir)
        self.process_logger = ProcessMiningLogger(log_dir="process_logs")

    def _load_config(self) -> dict:
        config_path = self.task_dir / "config.yaml"
        if config_path.exists():
            return yaml.safe_load(config_path.read_text(encoding='utf-8'))
        return {}

    def execute(self):
        task_name = self.config.get('name', 'unknown')
        company_name = self.config.get('company', 'unknown')
        audit_type = self.config.get('audit_type', 'it')

        process_start = self.process_logger.log_process_start(
            process_name=f"Audit_{task_name}",
            data={
                "task_name": task_name,
                "company": company_name,
                "audit_type": audit_type,
                "status": "started"
            }
        )

        try:
            self.logger.info(f"Executing task: {task_name}")

            # Validate configuration before proceeding
            validation = InputValidator.validate_task_config(self.config)
            self.process_logger.log_event(
                process_name=f"Audit_{task_name}",
                stage="Configuration_Validation",
                start_time=process_start.start_time,
                end_time=datetime.now(),
                data={
                    "is_valid": validation.is_valid,
                    "error_count": len(validation.errors),
                    "warning_count": len(validation.warnings)
                }
            )

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
            report_start = datetime.now()
            self.orchestrator.generate(findings)

            self.process_logger.log_event(
                process_name=f"Audit_{task_name}",
                stage="Report_Generation",
                start_time=report_start,
                end_time=datetime.now(),
                data={
                    "findings_count": len(findings),
                    "status": "completed"
                }
            )

            self.logger.info("Task completed successfully")

            # Log process end and save all formats
            self.process_logger.log_process_end(
                process_name=f"Audit_{task_name}",
                start_event=process_start,
                data={
                    "status": "success",
                    "task_name": task_name,
                    "company": company_name
                }
            )
            self.process_logger.save_all_formats()

        except AuditError as e:
            self.logger.error(f"Audit error in task '{task_name}': {str(e)}")
            self.process_logger.log_process_end(
                process_name=f"Audit_{task_name}",
                start_event=process_start,
                data={
                    "status": "failed",
                    "error": str(e),
                    "error_code": getattr(e, 'error_code', 'UNKNOWN')
                }
            )
            self.process_logger.save_all_formats()
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error in task '{task_name}': {str(e)}",
                exc_info=True
            )
            self.process_logger.log_process_end(
                process_name=f"Audit_{task_name}",
                start_event=process_start,
                data={
                    "status": "failed",
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            self.process_logger.save_all_formats()
            raise AuditError(
                f"Task execution failed: {str(e)}",
                error_code="TASK_EXECUTION_FAILED"
            ) from e
