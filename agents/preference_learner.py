"""Learn user preferences from Track Changes in revision history."""

from pathlib import Path
from collections import Counter
from typing import Optional

from agents.base import BaseAgent
from core.preferences import PreferencesStore, UserPreferences
from core.logger import setup_logger
from report_generator.docx import DocxImporter, VersionManager, RevisionRecord

logger = setup_logger("preference_learner")

MIN_FREQUENCY = 2  # Minimum repetitions to fix a substitution


class PreferenceLearner(BaseAgent):
    """Extract and persist user preferences from Track Changes history."""

    def __init__(self):
        """Initialize learner with preferences store."""
        try:
            super().__init__(name="preference_learner")
        except Exception as e:
            logger.warning(f"BaseAgent init failed (LLM unavailable): {e}. Continuing without LLM.")
        self.store = PreferencesStore()
        self.importer = DocxImporter()
        logger.info("PreferenceLearner initialized")

    def learn_from_revision(self, task_dir: Path) -> UserPreferences:
        """Extract preferences from task revision history.

        Process:
        1. Walk all versions in VersionManager
        2. Extract tracked_changes from each DOCX via DocxImporter
        3. Count (old_text → new_text) pairs
        4. Filter by MIN_FREQUENCY threshold
        5. Load existing per-task prefs and merge new substitutions
        6. Save updated per-task preferences

        Args:
            task_dir: Task directory path.

        Returns:
            Updated UserPreferences with learned terminology.
        """
        task_dir = Path(task_dir)
        task_name = task_dir.name

        logger.info(f"Learning preferences from revision history: {task_name}")

        # Collect all tracked changes across versions
        all_changes = self._collect_all_tracked_changes(task_dir)
        if not all_changes:
            logger.info(f"No tracked changes found for {task_name}")
            return self.store.load(task_name)

        # Extract substitutions above MIN_FREQUENCY
        substitutions = self._extract_substitutions(all_changes)
        logger.info(
            f"Extracted {len(substitutions)} term substitutions: {substitutions}"
        )

        # Load existing per-task prefs and merge
        current = self.store.load(task_name)
        current.terminology.update(substitutions)
        self.store.save(current, task_name)

        logger.info(f"Preferences updated for {task_name}: {len(current.terminology)} terms")
        return current

    def _collect_all_tracked_changes(self, task_dir: Path) -> list[RevisionRecord]:
        """Walk all versions and collect tracked changes.

        Args:
            task_dir: Task directory.

        Returns:
            List of all RevisionRecords across versions.
        """
        vm = VersionManager(task_dir)
        all_changes = []

        for version in vm.list_versions():
            docx_path = vm.get_version(version)
            if not docx_path or not docx_path.exists():
                logger.debug(f"DOCX not found for version {version}: {docx_path}")
                continue

            try:
                # Extract feedback (includes tracked_changes)
                prior_md_path = task_dir / "output" / "Audit_Report.md"
                feedback = self.importer.extract_feedback(docx_path, prior_md_path)
                all_changes.extend(feedback.tracked_changes)
                logger.debug(
                    f"Version {version}: extracted {len(feedback.tracked_changes)} changes"
                )
            except Exception as e:
                logger.warning(f"Failed to extract feedback from version {version}: {e}")

        return all_changes

    def _extract_substitutions(self, changes: list[RevisionRecord]) -> dict[str, str]:
        """Count (old_text → new_text) pairs and filter by frequency.

        Only include substitutions that occur at least MIN_FREQUENCY times.

        Args:
            changes: List of RevisionRecord from tracked_changes.

        Returns:
            Dict mapping old_text → new_text for frequent substitutions.
        """
        if not changes:
            return {}

        # Count (old, new) pairs
        counts = Counter((c.old_text, c.new_text) for c in changes)

        # Filter by MIN_FREQUENCY
        result = {
            old: new
            for (old, new), count in counts.items()
            if count >= MIN_FREQUENCY and old != new
        }

        logger.debug(f"Substitution frequency: {dict(counts)}")
        return result

    def execute(self, task: str) -> str:
        """Placeholder to satisfy BaseAgent ABC. Use learn_from_revision() instead."""
        raise NotImplementedError("Use learn_from_revision() method directly")
