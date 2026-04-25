import shutil
from pathlib import Path
from typing import Optional
from core.config import PROJECT_ROOT
from core.logger import setup_logger
from knowledge.indexer import VectorIndexer


class RequirementsIndexer:
    """Manage L1/L2/L3 requirement documents and index them into ChromaDB."""

    LEVEL_MAP = {
        1: ("regulatory", PROJECT_ROOT / "knowledge" / "requirements" / "regulatory"),
        2: ("audit_standard", PROJECT_ROOT / "knowledge" / "requirements" / "audit"),
        3: ("local_policy", PROJECT_ROOT / "knowledge" / "requirements" / "local"),
    }

    def __init__(self):
        self.logger = setup_logger("requirements_indexer")
        self.indexer = VectorIndexer()

    def add_requirement(
        self,
        file_path: str | Path,
        level: int,
        authority: Optional[str] = None
    ) -> int:
        """Copy requirement file to level folder and index into ChromaDB.

        Args:
            file_path: Path to requirement document (PDF, TXT, MD, etc.)
            level: Requirement level (1=regulatory, 2=audit_standard, 3=local_policy)
            authority: Authority/source (ISO, ISACA, FSTEC, Brink's, internal, user_defined)

        Returns:
            Number of chunks indexed

        Raises:
            ValueError: If level is not 1, 2, or 3
            FileNotFoundError: If source file doesn't exist
        """
        if level not in self.LEVEL_MAP:
            raise ValueError(f"Invalid requirement level: {level}. Must be 1, 2, or 3.")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Requirement file not found: {file_path}")

        doc_type, folder = self.LEVEL_MAP[level]
        folder.mkdir(parents=True, exist_ok=True)

        # Copy file to requirements folder
        dest = folder / file_path.name
        shutil.copy2(file_path, dest)
        self.logger.info(f"Copied requirement to {dest}")

        # Index into ChromaDB
        authority = authority or "user_defined"
        chunks = self.indexer.index_file(
            dest,
            doc_type=doc_type,
            req_level=level,
            authority=authority
        )

        self.logger.info(f"Indexed {chunks} chunks for L{level} ({authority})")
        return chunks

    def list_requirements(self, level: Optional[int] = None) -> dict[int, list[str]]:
        """List requirement files by level.

        Args:
            level: Specific level to list (1/2/3), or None for all levels

        Returns:
            Dictionary mapping level → list of filenames
        """
        result = {}
        levels = [level] if level else [1, 2, 3]

        for lvl in levels:
            _, folder = self.LEVEL_MAP[lvl]
            if not folder.exists():
                result[lvl] = []
            else:
                result[lvl] = sorted([f.name for f in folder.glob("*") if f.is_file()])

        self.logger.debug(f"Listed requirements: {result}")
        return result

    def index_all(self) -> dict[int, int]:
        """Re-index all requirement folders into ChromaDB.

        Returns:
            Dictionary mapping level → total chunk count
        """
        counts = {}

        for lvl, (doc_type, folder) in self.LEVEL_MAP.items():
            if not folder.exists():
                counts[lvl] = 0
                continue

            total = 0
            for file_path in folder.glob("*"):
                if file_path.is_file():
                    try:
                        chunks = self.indexer.index_file(
                            file_path,
                            doc_type=doc_type,
                            req_level=lvl
                        )
                        total += chunks
                    except Exception as e:
                        self.logger.warning(f"Failed to index {file_path}: {e}")

            counts[lvl] = total
            self.logger.info(f"Indexed L{lvl}: {total} chunks")

        return counts
