import os
import json
import hashlib
from pathlib import Path
from typing import Optional
from core.logger import setup_logger

class DocumentFetcher:
    def __init__(self, registry_path: str = None):
        if registry_path is None:
            registry_path = Path(__file__).parent / "document_registry.json"
        self.registry_path = Path(registry_path)
        self.raw_docs_path = Path(__file__).parent / "raw_docs"
        self.raw_docs_path.mkdir(exist_ok=True)
        self.logger = setup_logger("fetcher")
        self.registry = self._load_registry()
    
    def _load_registry(self) -> dict:
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_registry(self):
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)
    
    def get_or_fetch(self, query: str, doc_type: str) -> Optional[Path]:
        cache_key = hashlib.md5(f"{query}_{doc_type}".encode()).hexdigest()
        if cache_key in self.registry:
            cached_path = Path(self.registry[cache_key])
            if cached_path.exists():
                self.logger.info(f"Cache hit: {cached_path}")
                return cached_path
        self.logger.info(f"Cache miss: {query}")
        return None
