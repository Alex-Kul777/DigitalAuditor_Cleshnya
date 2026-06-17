"""Tests for preferences management system."""

import tempfile
import json
from pathlib import Path

import pytest
import yaml

from core.preferences import UserPreferences, PreferencesStore
from agents.preference_learner import PreferenceLearner, MIN_FREQUENCY
from report_generator.docx import RevisionRecord


class TestUserPreferencesDataclass:
    """Test UserPreferences dataclass."""

    def test_defaults(self):
        """Test default values."""
        prefs = UserPreferences()
        assert prefs.terminology == {}
        assert prefs.findings_count == 5
        assert prefs.detail_level == "standard"
        assert prefs.tone == "official"
        assert prefs.sections_include == []
        assert prefs.sections_exclude == []

    def test_to_dict(self):
        """Test serialization to dict."""
        prefs = UserPreferences(
            terminology={"риск": "угроза"},
            findings_count=3,
            tone="technical"
        )
        d = prefs.to_dict()
        assert d["terminology"] == {"риск": "угроза"}
        assert d["findings_count"] == 3
        assert d["tone"] == "technical"

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "terminology": {"риск": "угроза"},
            "findings_count": 3,
            "tone": "business",
        }
        prefs = UserPreferences.from_dict(data)
        assert prefs.terminology == {"риск": "угроза"}
        assert prefs.findings_count == 3
        assert prefs.tone == "business"

    def test_from_dict_empty(self):
        """Test from_dict with None/empty."""
        prefs = UserPreferences.from_dict(None)
        assert prefs.findings_count == 5
        assert prefs.terminology == {}


class TestPreferencesStoreLoad:
    """Test PreferencesStore.load()."""

    def test_load_returns_defaults_when_no_files(self):
        """Test load returns defaults when no preference files exist."""
        store = PreferencesStore()
        prefs = store.load()
        assert prefs.terminology == {}
        assert prefs.findings_count == 5

    def test_load_global_yaml(self, tmp_path):
        """Test loading global preferences from YAML."""
        # Temporarily override GLOBAL_PATH
        global_yaml = tmp_path / "user_preferences.yaml"
        global_yaml.write_text(
            yaml.dump({
                "terminology": {"риск": "угроза"},
                "findings_count": 3,
            }),
            encoding="utf-8"
        )

        store = PreferencesStore()
        store.GLOBAL_PATH = global_yaml
        prefs = store.load()

        assert prefs.terminology == {"риск": "угроза"}
        assert prefs.findings_count == 3

    def test_load_per_task_overrides_global(self, monkeypatch, tmp_path):
        """Test per-task preferences override global."""
        global_yaml = tmp_path / "user_preferences.yaml"
        global_yaml.write_text(
            yaml.dump({"terminology": {"риск": "угроза"}, "findings_count": 5}),
            encoding="utf-8"
        )

        task_dir = tmp_path / "tasks" / "instances" / "test_task"
        task_dir.mkdir(parents=True, exist_ok=True)
        task_yaml = task_dir / "preferences.yaml"
        task_yaml.write_text(
            yaml.dump({"findings_count": 3}),
            encoding="utf-8"
        )

        # Mock PROJECT_ROOT
        from core import preferences as pref_module
        monkeypatch.setattr(pref_module, "PROJECT_ROOT", tmp_path)

        store = PreferencesStore()
        # Fix path resolution for task_dir
        monkeypatch.setattr(store, "GLOBAL_PATH", global_yaml)

        prefs = store.load(task_name="test_task")

        # Should have global terminology + per-task findings_count
        assert prefs.terminology == {"риск": "угроза"}
        assert prefs.findings_count == 3


class TestPreferencesStoreMerge:
    """Test PreferencesStore._merge()."""

    def test_merge_per_task_beats_global(self):
        """Test that per-task overrides beat global."""
        global_prefs = UserPreferences(
            terminology={"риск": "угроза"},
            findings_count=5,
            tone="official"
        )
        task_prefs = UserPreferences(
            findings_count=3,
            tone="technical"
        )

        store = PreferencesStore()
        merged = store._merge(global_prefs, task_prefs)

        assert merged.findings_count == 3  # from per-task
        assert merged.tone == "technical"  # from per-task
        assert merged.terminology == {"риск": "угроза"}  # from global (unchanged)

    def test_merge_terminology_dicts_merged(self):
        """Test that terminology dicts are merged, per-task wins on conflict."""
        global_prefs = UserPreferences(
            terminology={"риск": "угроза", "контроль": "мера"}
        )
        task_prefs = UserPreferences(
            terminology={"риск": "опасность"}  # override global
        )

        store = PreferencesStore()
        merged = store._merge(global_prefs, task_prefs)

        assert merged.terminology["риск"] == "опасность"  # from per-task
        assert merged.terminology["контроль"] == "мера"  # from global


class TestPreferencesStoreSave:
    """Test PreferencesStore.save()."""

    def test_save_creates_yaml_file(self, tmp_path):
        """Test save creates YAML file with correct content."""
        prefs = UserPreferences(
            terminology={"риск": "угроза"},
            findings_count=3,
            tone="technical"
        )

        store = PreferencesStore()
        store.GLOBAL_PATH = tmp_path / "global.yaml"

        saved_path = store.save(prefs)

        assert saved_path.exists()
        loaded_data = yaml.safe_load(saved_path.read_text(encoding="utf-8"))
        assert loaded_data["terminology"] == {"риск": "угроза"}
        assert loaded_data["findings_count"] == 3

    def test_save_per_task(self, monkeypatch, tmp_path):
        """Test save to per-task path."""
        task_root = tmp_path / "tasks" / "instances"
        task_root.mkdir(parents=True, exist_ok=True)

        prefs = UserPreferences(findings_count=3)

        # Mock PROJECT_ROOT
        from core import preferences as pref_module
        monkeypatch.setattr(pref_module, "PROJECT_ROOT", tmp_path)

        store = PreferencesStore()
        saved_path = store.save(prefs, task_name="test_task")

        # Should save to tasks/instances/test_task/preferences.yaml
        assert saved_path.name == "preferences.yaml"
        assert "test_task" in str(saved_path)
        assert saved_path.exists()


class TestPreferencesLoadFile:
    """Test PreferencesStore._load_file()."""

    def test_load_file_missing_returns_defaults(self):
        """Test _load_file returns defaults when file missing."""
        store = PreferencesStore()
        prefs = store._load_file(Path("/nonexistent/path.yaml"))
        assert prefs.findings_count == 5

    def test_load_file_corrupted_returns_defaults(self, tmp_path):
        """Test _load_file returns defaults on YAML error."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("{ invalid yaml :", encoding="utf-8")

        store = PreferencesStore()
        prefs = store._load_file(bad_yaml)
        assert prefs.findings_count == 5


class TestPreferenceLearnerExtractSubstitutions:
    """Test PreferenceLearner._extract_substitutions()."""

    def test_extract_substitutions_counts_frequency(self, mocker):
        """Test frequency counting of (old → new) pairs."""
        mocker.patch("agents.preference_learner.BaseAgent.__init__", return_value=None)

        changes = [
            RevisionRecord("риск", "угроза", "user", "2026-04-25", "edit"),
            RevisionRecord("риск", "угроза", "user", "2026-04-25", "edit"),
            RevisionRecord("контроль", "мера", "user", "2026-04-25", "edit"),
            RevisionRecord("контроль", "мера", "user", "2026-04-25", "edit"),
        ]

        learner = PreferenceLearner()
        subs = learner._extract_substitutions(changes)

        # Both have frequency >= MIN_FREQUENCY (2)
        assert "риск" in subs
        assert subs["риск"] == "угроза"
        assert "контроль" in subs
        assert subs["контроль"] == "мера"

    def test_extract_substitutions_filters_below_min_freq(self, mocker):
        """Test that substitutions below MIN_FREQUENCY are filtered out."""
        mocker.patch("agents.preference_learner.BaseAgent.__init__", return_value=None)

        changes = [
            RevisionRecord("rare", "replacement", "user", "2026-04-25", "edit"),
            # Only 1 occurrence, below MIN_FREQUENCY=2
        ]

        learner = PreferenceLearner()
        subs = learner._extract_substitutions(changes)

        assert "rare" not in subs

    def test_extract_substitutions_empty_changes(self, mocker):
        """Test with empty changes list."""
        mocker.patch("agents.preference_learner.BaseAgent.__init__", return_value=None)

        learner = PreferenceLearner()
        subs = learner._extract_substitutions([])
        assert subs == {}

    def test_extract_substitutions_ignores_identity(self, mocker):
        """Test that old_text == new_text is filtered out."""
        mocker.patch("agents.preference_learner.BaseAgent.__init__", return_value=None)

        changes = [
            RevisionRecord("same", "same", "user", "2026-04-25", "edit"),
            RevisionRecord("same", "same", "user", "2026-04-25", "edit"),
        ]

        learner = PreferenceLearner()
        subs = learner._extract_substitutions(changes)

        assert "same" not in subs


class TestPreferenceLearnerLearnFromRevision:
    """Test PreferenceLearner.learn_from_revision()."""

    def test_learn_from_revision_saves_to_per_task(self, mocker, monkeypatch, tmp_path):
        """Test that learned preferences are saved to per-task store."""
        mocker.patch("agents.preference_learner.BaseAgent.__init__", return_value=None)
        from core import preferences as pref_module
        monkeypatch.setattr(pref_module, "PROJECT_ROOT", tmp_path)

        task_dir = tmp_path / "test_task"
        task_dir.mkdir(parents=True, exist_ok=True)

        # Create mock version/DOCX (skipping full setup for unit test)
        versions_dir = task_dir / "versions"
        versions_dir.mkdir()

        learner = PreferenceLearner()
        # Mock the _collect_all_tracked_changes to return test data
        learner._collect_all_tracked_changes = lambda td: [
            RevisionRecord("риск", "угроза", "user", "2026-04-25", "edit"),
            RevisionRecord("риск", "угроза", "user", "2026-04-25", "edit"),
        ]

        prefs = learner.learn_from_revision(task_dir)

        assert "риск" in prefs.terminology
        assert prefs.terminology["риск"] == "угроза"

    def test_learn_from_revision_merges_with_existing(self, mocker, monkeypatch, tmp_path):
        """Test that new learning merges with existing preferences."""
        mocker.patch("agents.preference_learner.BaseAgent.__init__", return_value=None)
        from core import preferences as pref_module
        monkeypatch.setattr(pref_module, "PROJECT_ROOT", tmp_path)

        # Create task structure under tmp_path
        task_instances = tmp_path / "tasks" / "instances" / "test_task"
        task_instances.mkdir(parents=True, exist_ok=True)
        (task_instances / "versions").mkdir()

        # Create existing per-task prefs
        prefs_yaml = task_instances / "preferences.yaml"
        prefs_yaml.write_text(
            yaml.dump({"terminology": {"контроль": "мера"}}),
            encoding="utf-8"
        )

        learner = PreferenceLearner()
        learner._collect_all_tracked_changes = lambda td: [
            RevisionRecord("риск", "угроза", "user", "2026-04-25", "edit"),
            RevisionRecord("риск", "угроза", "user", "2026-04-25", "edit"),
        ]

        prefs = learner.learn_from_revision(task_instances)

        # Should have both old and new terminology
        assert prefs.terminology["контроль"] == "мера"
        assert prefs.terminology["риск"] == "угроза"
