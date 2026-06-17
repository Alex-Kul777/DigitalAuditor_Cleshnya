"""Revision agent: apply feedback to audit reports and generate revised versions."""

from pathlib import Path
from typing import Optional

from agents.base import BaseAgent
from core.llm import LLMFactory
from core.logger import setup_logger
from report_generator.docx import (
    DocxExporter,
    DocxImporter,
    VersionManager,
    Feedback,
)

logger = setup_logger("revision_agent")


class RevisionAgent(BaseAgent):
    """Apply user feedback to audit reports and generate revised versions."""

    def __init__(self, temperature: float = 0.3):
        """Initialize revision agent.

        Args:
            temperature: LLM temperature for edits (conservative by default)
        """
        super().__init__(name="revision_agent")
        self.llm = LLMFactory.get_llm(temperature=temperature)
        self.exporter = DocxExporter()
        self.importer = DocxImporter()
        logger.info("RevisionAgent initialized")

    def revise(self, task_dir: Path, feedback: Optional[Feedback] = None) -> Path:
        """Revise audit report based on feedback.

        Process:
        1. Load prior MD (from feedback.source_md or from output/)
        2. Apply user comments + tracked changes via LLM
        3. Generate revised MD
        4. Re-export to DOCX with AI edits as Track Changes
        5. Save version via VersionManager
        6. Return path to revised DOCX

        Args:
            task_dir: Task directory
            feedback: Feedback from DocxImporter. If None, load from latest DOCX

        Returns:
            Path to revised DOCX
        """
        task_dir = Path(task_dir)
        vm = VersionManager(task_dir)

        # If no feedback provided, extract from latest DOCX
        if feedback is None:
            latest_docx = vm.latest()
            if not latest_docx:
                raise FileNotFoundError("No prior DOCX found to revise")

            prior_md_path = task_dir / "output" / "Audit_Report.md"
            if not prior_md_path.exists():
                raise FileNotFoundError(f"Prior MD not found: {prior_md_path}")

            feedback = self.importer.extract_feedback(latest_docx, prior_md_path)
            logger.info(f"Loaded feedback from {latest_docx}")

        # Apply revisions via LLM
        revised_md = self._apply_feedback(
            feedback.source_md,
            feedback.comments_by_user,
            feedback.tracked_changes,
        )

        # Re-export to DOCX
        revised_docx_path = task_dir / "output" / "Audit_Report_Revised.docx"
        self.exporter.backend.md_to_docx(revised_md, revised_docx_path)
        logger.info(f"Re-exported to DOCX: {revised_docx_path}")

        # Save version
        next_version = vm.next_version()
        vm.save(next_version, revised_md, revised_docx_path)
        logger.info(f"Saved version {next_version}")

        # Auto-learn preferences from this revision
        try:
            from agents.preference_learner import PreferenceLearner
            learner = PreferenceLearner()
            learned = learner.learn_from_revision(task_dir)
            if learned.terminology:
                logger.info(f"Preferences learned: {len(learned.terminology)} term substitutions")
        except Exception as e:
            logger.warning(f"Preference learning failed: {e}")

        return revised_docx_path

    def _apply_feedback(self, source_md: str, user_comments, tracked_changes) -> str:
        """Apply user feedback to source MD.

        Strategy:
        - For each user comment: identify location, generate LLM suggestion, apply
        - For each tracked change: apply directly
        - Preserve structure, update only flagged sections

        Args:
            source_md: Source markdown
            user_comments: List of CommentRecords from users
            tracked_changes: List of RevisionRecords from tracked changes

        Returns:
            Revised markdown
        """
        revised = source_md

        # Apply tracked changes first (explicit edits)
        for change in tracked_changes:
            if change.old_text in revised:
                logger.debug(f"Applying tracked change: {change.old_text[:40]} → {change.new_text[:40]}")
                revised = revised.replace(change.old_text, change.new_text, 1)

        # Apply user comments via LLM
        for comment in user_comments:
            anchor = comment.anchor_text
            if anchor in revised:
                # Find section to revise (paragraph containing anchor)
                # Generate LLM suggestion for revision
                suggestion = self._generate_revision(anchor, comment.comment_text, source_md)

                if suggestion and suggestion != anchor:
                    logger.debug(f"Applying LLM revision for comment: {comment.author}")
                    revised = revised.replace(anchor, suggestion, 1)

        logger.info("Feedback applied to markdown")
        return revised

    def _generate_revision(self, anchor: str, comment: str, context: str) -> Optional[str]:
        """Generate LLM-guided revision for a paragraph.

        Args:
            anchor: Paragraph text to revise
            comment: User feedback comment
            context: Full markdown for context

        Returns:
            Revised paragraph text, or None if LLM fails
        """
        prompt = f"""Ты — редактор аудит-отчёта. Пользователь оставил замечание.

Оригинальный параграф:
<<<{anchor}>>>

Замечание пользователя:
{comment}

Переработай параграф учитывая замечание. Сохрани стиль и объём. Ответь ТОЛЬКО переработанным параграфом, без комментариев."""

        try:
            revision = self.llm.invoke(prompt)
            return revision.strip() if revision else None
        except Exception as e:
            logger.warning(f"LLM revision failed: {e}")
            return None

    def execute(self, task: str) -> str:
        """Placeholder to satisfy BaseAgent ABC. Use revise() instead."""
        raise NotImplementedError("Use revise() method directly")
