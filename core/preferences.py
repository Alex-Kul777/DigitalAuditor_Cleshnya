"""User preferences management — global + per-task with auto-learning from Track Changes."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional
from collections import Counter

from core.config import PROJECT_ROOT
from core.logger import setup_logger

logger = setup_logger("core.preferences")


@dataclass
class UserPreferences:
    """User personalization preferences across 4 categories."""

    # A — Терминология: автоматические замены
    terminology: dict[str, str] = field(default_factory=dict)

    # Б — Формат findings
    findings_count: int = 5
    detail_level: str = "standard"  # "brief" | "standard" | "detailed"

    # В — Тон/стиль
    tone: str = "official"  # "official" | "business" | "technical"

    # Г — Структура разделов
    sections_include: list[str] = field(default_factory=list)
    sections_exclude: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict for YAML serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserPreferences":
        """Create from dict (YAML deserialization)."""
        if not data:
            return cls()
        return cls(
            terminology=data.get("terminology", {}),
            findings_count=data.get("findings_count", 5),
            detail_level=data.get("detail_level", "standard"),
            tone=data.get("tone", "official"),
            sections_include=data.get("sections_include", []),
            sections_exclude=data.get("sections_exclude", []),
        )


class PreferencesStore:
    """Hybrid store: global + per-task preferences with merge."""

    GLOBAL_PATH = PROJECT_ROOT / "config" / "user_preferences.yaml"

    def __init__(self):
        """Initialize preferences store."""
        self.logger = logger

    def load(self, task_name: Optional[str] = None) -> UserPreferences:
        """Load preferences: global optionally merged with per-task override.

        Args:
            task_name: Optional task name. If provided, merge per-task override.

        Returns:
            UserPreferences: merged preferences (per-task beats global).
        """
        global_prefs = self._load_file(self.GLOBAL_PATH)

        if task_name:
            per_task_path = (
                PROJECT_ROOT / "tasks" / "instances" / task_name / "preferences.yaml"
            )
            task_prefs = self._load_file(per_task_path)
            return self._merge(global_prefs, task_prefs)

        return global_prefs

    def save(
        self, prefs: UserPreferences, task_name: Optional[str] = None
    ) -> Path:
        """Save preferences to global or per-task store.

        Args:
            prefs: UserPreferences object.
            task_name: If provided, save to per-task; else save to global.

        Returns:
            Path: path where saved.
        """
        if task_name:
            path = (
                PROJECT_ROOT / "tasks" / "instances" / task_name / "preferences.yaml"
            )
        else:
            path = self.GLOBAL_PATH

        path.parent.mkdir(parents=True, exist_ok=True)

        import yaml

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(prefs.to_dict(), f, default_flow_style=False, allow_unicode=True)

        self.logger.info(f"Preferences saved: {path}")
        return path

    def _merge(
        self, base: UserPreferences, override: UserPreferences
    ) -> UserPreferences:
        """Merge base + override, per-task beats global.

        For `terminology` dict: merge both, override wins on conflict.
        For other fields: override replaces base if not default.

        Args:
            base: Global preferences.
            override: Per-task preferences.

        Returns:
            Merged UserPreferences.
        """
        merged_terminology = {**base.terminology}
        merged_terminology.update(override.terminology)

        # Use override if it's not default, else use base
        merged = UserPreferences(
            terminology=merged_terminology,
            findings_count=override.findings_count if override.findings_count != 5 else base.findings_count,
            detail_level=override.detail_level if override.detail_level != "standard" else base.detail_level,
            tone=override.tone if override.tone != "official" else base.tone,
            sections_include=override.sections_include if override.sections_include else base.sections_include,
            sections_exclude=override.sections_exclude if override.sections_exclude else base.sections_exclude,
        )
        return merged

    def _load_file(self, path: Path) -> UserPreferences:
        """Load YAML preferences file. Returns defaults if missing.

        Args:
            path: Path to preferences YAML.

        Returns:
            UserPreferences: loaded or defaults.
        """
        if not path.exists():
            self.logger.debug(f"Preferences file not found: {path}, using defaults")
            return UserPreferences()

        try:
            import yaml

            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return UserPreferences.from_dict(data)
        except Exception as e:
            self.logger.warning(f"Failed to load preferences from {path}: {e}")
            return UserPreferences()
