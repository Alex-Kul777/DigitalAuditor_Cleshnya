"""Version management for audit report iterations."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from core.logger import setup_logger

logger = setup_logger("docx.version_manager")


class VersionManager:
    """Manage versioned audit reports with manifest tracking."""

    def __init__(self, task_dir: Path):
        """Initialize version manager for task.

        Args:
            task_dir: Root task directory (e.g., tasks/instances/gogol_audit)
        """
        self.task_dir = Path(task_dir)
        self.versions_dir = self.task_dir / "versions"
        self.output_dir = self.task_dir / "output"
        self.manifest_path = self.output_dir / "latest.json"

        # Ensure directories exist
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"VersionManager for {self.task_dir}")

    def next_version(self) -> int:
        """Get next version number.

        Returns:
            Next available version (1-based)
        """
        if not self.versions_dir.exists():
            return 1

        versions = [
            int(d.name[1:])
            for d in self.versions_dir.iterdir()
            if d.is_dir() and d.name.startswith('v') and d.name[1:].isdigit()
        ]

        return max(versions) + 1 if versions else 1

    def save(self, version: int, md_content: str, docx_path: Path) -> Path:
        """Save version to archive.

        Args:
            version: Version number
            md_content: Markdown source content
            docx_path: Path to generated DOCX file

        Returns:
            Path to saved DOCX in versions/vN/
        """
        vdir = self.versions_dir / f"v{version}"
        vdir.mkdir(parents=True, exist_ok=True)

        # Save source markdown
        source_file = vdir / "source.md"
        source_file.write_text(md_content, encoding='utf-8')
        logger.debug(f"Saved source MD: {source_file}")

        # Copy DOCX to version folder
        if not docx_path.exists():
            raise FileNotFoundError(f"DOCX not found: {docx_path}")

        docx_file = vdir / "report.docx"
        shutil.copy2(docx_path, docx_file)
        logger.debug(f"Saved DOCX: {docx_file}")

        # Update manifest
        self._update_manifest(version, docx_file)

        # Copy to output/Audit_Report.docx as latest
        latest_docx = self.output_dir / "Audit_Report.docx"
        shutil.copy2(docx_file, latest_docx)
        logger.info(f"Latest version symlink updated: {latest_docx}")

        return docx_file

    def _update_manifest(self, version: int, path: Path) -> None:
        """Update latest.json manifest.

        Args:
            version: Version number
            path: Absolute path to DOCX file
        """
        # Load existing history
        history = self._load_history()

        # Create new manifest
        manifest = {
            "current_version": version,
            "current_path": str(path.relative_to(self.output_dir.parent)),
            "updated_at": datetime.now().isoformat(),
            "history": history + [
                {
                    "version": version,
                    "path": str(path.relative_to(self.output_dir.parent)),
                    "saved_at": datetime.now().isoformat(),
                }
            ],
        }

        self.manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        logger.debug(f"Manifest updated: {self.manifest_path}")

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load version history from manifest.

        Returns:
            List of version records (empty if manifest doesn't exist)
        """
        if not self.manifest_path.exists():
            return []

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding='utf-8'))
            return manifest.get("history", [])
        except (json.JSONDecodeError, KeyError):
            logger.warning(f"Corrupted manifest: {self.manifest_path}")
            return []

    def latest(self) -> Optional[Path]:
        """Get path to latest version DOCX.

        Returns:
            Path to latest DOCX, or None if no versions saved
        """
        if not self.manifest_path.exists():
            return None

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding='utf-8'))
            path_str = manifest.get("current_path")
            if path_str:
                return self.task_dir.parent / path_str
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to read latest version from manifest")

        return None

    def get_version(self, version: int) -> Optional[Path]:
        """Get path to specific version DOCX.

        Args:
            version: Version number

        Returns:
            Path to version DOCX, or None if not found
        """
        vdir = self.versions_dir / f"v{version}"
        docx_path = vdir / "report.docx"

        if docx_path.exists():
            return docx_path

        return None

    def list_versions(self) -> List[int]:
        """List all available versions.

        Returns:
            Sorted list of version numbers
        """
        versions = []
        if self.versions_dir.exists():
            for d in self.versions_dir.iterdir():
                if d.is_dir() and d.name.startswith('v') and d.name[1:].isdigit():
                    versions.append(int(d.name[1:]))

        return sorted(versions)
