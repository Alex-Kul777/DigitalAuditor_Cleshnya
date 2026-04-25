import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from core.logger import setup_logger
from knowledge.indexer import VectorIndexer


class EvidenceIndexer:
    """Track and index evidence files with SHA-256 change detection."""

    STATE_FILENAME = ".index_state.json"
    SKIP_FILES = {STATE_FILENAME, "sources.txt"}

    def __init__(self, task_name: str, evidence_dir: Path):
        """Initialize EvidenceIndexer for a task.

        Args:
            task_name: Name of the audit task (used for metadata)
            evidence_dir: Path to task's evidence directory
        """
        self.task_name = task_name
        self.evidence_dir = Path(evidence_dir)
        self.state_file = self.evidence_dir / self.STATE_FILENAME
        self.indexer = VectorIndexer()
        self.logger = setup_logger("evidence_indexer")

    def _sha256(self, path: Path) -> str:
        """Compute SHA-256 hash of file."""
        hash_obj = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def _load_state(self) -> dict:
        """Load current index state from .index_state.json.

        Returns:
            Dict mapping {filename: {"sha256": "...", "indexed_at": "..."}}
        """
        if self.state_file.exists():
            try:
                return json.loads(self.state_file.read_text())
            except Exception as e:
                self.logger.warning(f"Failed to load state file: {e}")
                return {}
        return {}

    def _save_state(self, state: dict) -> None:
        """Save index state to .index_state.json."""
        self.state_file.write_text(json.dumps(state, indent=2))
        self.logger.debug(f"Saved state with {len(state)} files")

    def sync(self) -> dict[str, int]:
        """Sync evidence directory: index new/changed files incrementally.

        Files are skipped if their SHA-256 hash matches the stored state.
        Automatically updates .index_state.json with new hashes.

        Returns:
            Dictionary mapping {filename: chunk_count} for indexed files
        """
        self.logger.info(f"Syncing evidence for task: {self.task_name}")
        state = self._load_state()
        results = {}

        # Ensure directory exists
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

        for file_path in self.evidence_dir.iterdir():
            # Skip directories and special files
            if not file_path.is_file() or file_path.name in self.SKIP_FILES:
                continue

            try:
                sha = self._sha256(file_path)

                # Check if file has changed
                if state.get(file_path.name, {}).get("sha256") == sha:
                    self.logger.debug(f"Skipped (unchanged): {file_path.name}")
                    continue

                # Index the file
                self.logger.info(f"Indexing: {file_path.name}")
                chunks = self.indexer.index_file(
                    file_path,
                    doc_type="evidence",
                    task_name=self.task_name
                )

                # Update state
                state[file_path.name] = {
                    "sha256": sha,
                    "indexed_at": datetime.now().isoformat()
                }
                results[file_path.name] = chunks

            except Exception as e:
                self.logger.warning(f"Failed to index {file_path.name}: {e}")

        # Save updated state
        self._save_state(state)
        self.logger.info(f"Sync complete: indexed {len(results)} files")

        return results

    def get_status(self) -> dict:
        """Get current sync status.

        Returns:
            Dict with:
            - total_files: count of evidence files (excluding skipped)
            - indexed_files: count of indexed files
            - total_chunks: total chunks indexed (from state)
            - last_indexed: timestamp of last sync
        """
        state = self._load_state()
        total_files = len([f for f in self.evidence_dir.iterdir()
                          if f.is_file() and f.name not in self.SKIP_FILES])

        return {
            "task_name": self.task_name,
            "total_files": total_files,
            "indexed_files": len(state),
            "last_indexed": max(
                (v.get("indexed_at") for v in state.values() if v.get("indexed_at")),
                default=None
            )
        }
