from pathlib import Path
import yaml
from core.logger import setup_logger
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
        self.logger.info(f"Executing task: {self.config.get('name', 'unknown')}")
        findings = []
        self.orchestrator.generate(findings)
        self.logger.info("Task completed")
