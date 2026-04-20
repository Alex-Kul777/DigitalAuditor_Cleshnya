import json
from pathlib import Path
from datetime import datetime

class EvidenceTracker:
    def __init__(self, task_dir: Path):
        self.evidence_file = task_dir / "evidence" / "evidence_log.json"
        self.evidence = self._load()
    
    def _load(self) -> list:
        if self.evidence_file.exists():
            return json.loads(self.evidence_file.read_text())
        return []
    
    def _save(self):
        self.evidence_file.write_text(json.dumps(self.evidence, indent=2, ensure_ascii=False))
    
    def add(self, source: str, content: str, relevance: str):
        self.evidence.append({
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "content": content,
            "relevance": relevance
        })
        self._save()
