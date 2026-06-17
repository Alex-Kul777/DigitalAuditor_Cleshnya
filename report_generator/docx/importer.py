"""DOCX importer: extract feedback (comments, tracked changes) from DOCX."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

from core.logger import setup_logger
from report_generator.docx.backends import DocxBackend, get_backend, CommentRecord, RevisionRecord

logger = setup_logger("docx.importer")


@dataclass
class Feedback:
    """Extracted feedback from DOCX review."""
    comments_by_agent: List[CommentRecord]  # author in known personas
    comments_by_user: List[CommentRecord]   # author not in personas
    tracked_changes: List[RevisionRecord]
    source_md: str                          # prior version markdown


class DocxImporter:
    """Import user feedback from DOCX (comments, tracked changes)."""

    def __init__(self, backend: DocxBackend = None):
        """Initialize importer with backend.

        Args:
            backend: DocxBackend instance. If None, auto-select via get_backend("auto")
        """
        self.backend = backend or get_backend("auto")
        logger.info(f"DocxImporter initialized with {self.backend.__class__.__name__}")

    def extract_feedback(self, docx_path: Path, prior_md_path: Path) -> Feedback:
        """Extract feedback from reviewed DOCX.

        Args:
            docx_path: Path to reviewed DOCX file
            prior_md_path: Path to source MD (for reference)

        Returns:
            Feedback with separated agent/user comments and tracked changes
        """
        if not docx_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {docx_path}")
        if not prior_md_path.exists():
            raise FileNotFoundError(f"Prior MD file not found: {prior_md_path}")

        # Extract all comments and changes
        all_comments = self.backend.read_comments(docx_path)
        tracked_changes = self.backend.read_tracked_changes(docx_path)
        source_md = prior_md_path.read_text(encoding='utf-8')

        # Separate agent vs user comments
        agent_comments, user_comments = self._separate_comments(all_comments)

        logger.info(
            f"Extracted feedback: {len(agent_comments)} agent comments, "
            f"{len(user_comments)} user comments, {len(tracked_changes)} tracked changes"
        )

        return Feedback(
            comments_by_agent=agent_comments,
            comments_by_user=user_comments,
            tracked_changes=tracked_changes,
            source_md=source_md,
        )

    def _separate_comments(self, comments: List[CommentRecord]) -> tuple:
        """Separate comments by agent vs user.

        Args:
            comments: All extracted comments

        Returns:
            (agent_comments, user_comments) tuples
        """
        try:
            from knowledge.persona_indexer import PersonaIndexer
            known_personas = set(PersonaIndexer().list_personas())
        except Exception as e:
            logger.warning(f"Failed to load persona registry: {e}. Treating all as user comments.")
            known_personas = set()

        agent_comments = [c for c in comments if c.author in known_personas]
        user_comments = [c for c in comments if c.author not in known_personas]

        return agent_comments, user_comments
