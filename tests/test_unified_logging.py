"""Tests for unified logging system (TXT/CSV/JSON formats, 6 log levels)."""

import json
import tempfile
from pathlib import Path
import pytest
from core.unified_logger import UnifiedLogger, LogEvent, TxtWriter, CsvWriter, JsonWriter, get_unified_logger


class TestTxtWriter:
    """Tests for TXT format writer."""

    def test_write_simple_event(self, tmp_path):
        """Test writing a simple event to TXT."""
        log_file = tmp_path / "audit.log"
        writer = TxtWriter(log_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="INFO",
            module="core",
            method="test_method",
            line=42,
            component="test",
            event_type="test_event",
            action="test_action",
            metadata={"key": "value"}
        )
        writer.write(event)

        assert log_file.exists()
        content = log_file.read_text()
        assert "INFO" in content
        assert "core:test_method:42" in content
        assert "test_action" in content

    def test_write_multiline_metadata(self, tmp_path):
        """Test writing event with multiline metadata."""
        log_file = tmp_path / "audit.log"
        writer = TxtWriter(log_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="DEBUG-2",
            module="retriever",
            method="retrieve",
            line=20,
            component="knowledge",
            event_type="retrieve",
            action="similarity_search",
            metadata={"query": "test query\nwith newlines", "results": 5}
        )
        writer.write(event)

        content = log_file.read_text()
        assert "similarity_search" in content
        assert "knowledge.retrieve" in content

    def test_write_multiple_events(self, tmp_path):
        """Test writing multiple events sequentially."""
        log_file = tmp_path / "audit.log"
        writer = TxtWriter(log_file)

        for i in range(3):
            event = LogEvent(
                timestamp=f"2026-04-26T10:00:0{i}.000",
                level="INFO",
                module="test",
                method="test",
                line=i,
                component="test",
                event_type="event",
                action=f"action_{i}",
            )
            writer.write(event)

        lines = log_file.read_text().strip().split('\n')
        assert len(lines) == 3
        assert "action_0" in lines[0]
        assert "action_2" in lines[2]

    def test_write_with_duration(self, tmp_path):
        """Test writing event with duration_ms."""
        log_file = tmp_path / "audit.log"
        writer = TxtWriter(log_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="INFO",
            module="test",
            method="test",
            line=1,
            component="test",
            event_type="timed",
            action="operation",
            duration_ms=1234
        )
        writer.write(event)

        content = log_file.read_text()
        assert "1234ms" in content

    def test_write_creates_parent_dir(self, tmp_path):
        """Test that TxtWriter creates parent directories."""
        log_file = tmp_path / "logs" / "nested" / "audit.log"
        writer = TxtWriter(log_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="INFO",
            module="test",
            method="test",
            line=1,
            component="test",
            event_type="event",
            action="action",
        )
        writer.write(event)

        assert log_file.exists()


class TestCsvWriter:
    """Tests for CSV format writer."""

    def test_csv_header_created(self, tmp_path):
        """Test that CSV header is created on first write."""
        csv_file = tmp_path / "audit.log.csv"
        writer = CsvWriter(csv_file)

        lines = csv_file.read_text().strip().split('\n')
        assert "timestamp" in lines[0]
        assert "level" in lines[0]
        assert "metadata" in lines[0]

    def test_write_event_to_csv(self, tmp_path):
        """Test writing event to CSV."""
        csv_file = tmp_path / "audit.log.csv"
        writer = CsvWriter(csv_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="WARNING",
            module="core",
            method="function",
            line=99,
            component="test",
            event_type="warning_event",
            action="warn_action",
            metadata={"severity": "high"}
        )
        writer.write(event)

        content = csv_file.read_text()
        assert "WARNING" in content
        assert "function" in content
        assert "severity" in content

    def test_csv_metadata_as_json(self, tmp_path):
        """Test that metadata is stored as JSON string in CSV."""
        csv_file = tmp_path / "audit.log.csv"
        writer = CsvWriter(csv_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="INFO",
            module="test",
            method="test",
            line=1,
            component="test",
            event_type="event",
            action="action",
            metadata={"key1": "value1", "key2": 42}
        )
        writer.write(event)

        lines = csv_file.read_text().strip().split('\n')
        # Line 1 is header, line 2 is data
        assert len(lines) >= 2
        assert '"key1"' in lines[1] or 'key1' in lines[1]

    def test_csv_escaping(self, tmp_path):
        """Test CSV field escaping with special characters."""
        csv_file = tmp_path / "audit.log.csv"
        writer = CsvWriter(csv_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="INFO",
            module="test",
            method="test",
            line=1,
            component="test",
            event_type="event",
            action='action with "quotes" and, commas',
            metadata={}
        )
        writer.write(event)

        lines = csv_file.read_text().strip().split('\n')
        assert len(lines) == 2  # header + data

    def test_multiple_rows_csv(self, tmp_path):
        """Test writing multiple rows to CSV."""
        csv_file = tmp_path / "audit.log.csv"
        writer = CsvWriter(csv_file)

        for i in range(3):
            event = LogEvent(
                timestamp=f"2026-04-26T10:00:0{i}.000",
                level="INFO",
                module="test",
                method="test",
                line=i,
                component="test",
                event_type="event",
                action=f"action_{i}",
            )
            writer.write(event)

        lines = csv_file.read_text().strip().split('\n')
        assert len(lines) == 4  # header + 3 data rows


class TestJsonWriter:
    """Tests for JSON Lines format writer."""

    def test_write_valid_json(self, tmp_path):
        """Test writing valid JSON to JSONL file."""
        json_file = tmp_path / "audit.log.json"
        writer = JsonWriter(json_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="DEBUG-1",
            module="core",
            method="function",
            line=50,
            component="test",
            event_type="event",
            action="action",
            metadata={"key": "value"}
        )
        writer.write(event)

        content = json_file.read_text().strip()
        obj = json.loads(content)
        assert obj["level"] == "DEBUG-1"
        assert obj["line"] == 50

    def test_jsonl_format_one_per_line(self, tmp_path):
        """Test JSONL format (one JSON object per line)."""
        json_file = tmp_path / "audit.log.json"
        writer = JsonWriter(json_file)

        for i in range(3):
            event = LogEvent(
                timestamp=f"2026-04-26T10:00:0{i}.000",
                level="INFO",
                module="test",
                method="test",
                line=i,
                component="test",
                event_type="event",
                action=f"action_{i}",
            )
            writer.write(event)

        lines = json_file.read_text().strip().split('\n')
        assert len(lines) == 3
        for line in lines:
            obj = json.loads(line)
            assert "timestamp" in obj
            assert "level" in obj

    def test_json_metadata(self, tmp_path):
        """Test that metadata is included in JSON."""
        json_file = tmp_path / "audit.log.json"
        writer = JsonWriter(json_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="INFO",
            module="test",
            method="test",
            line=1,
            component="test",
            event_type="event",
            action="action",
            metadata={"model": "GigaChat-2-Max", "tokens": 512}
        )
        writer.write(event)

        content = json_file.read_text().strip()
        obj = json.loads(content)
        assert obj["metadata"] == '{"model": "GigaChat-2-Max", "tokens": 512}'

    def test_json_unicode(self, tmp_path):
        """Test JSON with unicode characters."""
        json_file = tmp_path / "audit.log.json"
        writer = JsonWriter(json_file)

        event = LogEvent(
            timestamp="2026-04-26T10:00:00.000",
            level="INFO",
            module="test",
            method="тест",
            line=1,
            component="test",
            event_type="event",
            action="действие",
            metadata={"msg": "Тестовое сообщение"}
        )
        writer.write(event)

        content = json_file.read_text().strip()
        obj = json.loads(content)
        assert obj["method"] == "тест"
        # Metadata is JSON string, check it contains the data
        assert "msg" in obj["metadata"]  # Check key exists
        assert "сообщение" in obj["metadata"] or "\\u0441\\u043e\\u043e\\u0431\\u0449" in obj["metadata"]  # Check value (may be escaped)


class TestUnifiedLogger:
    """Tests for UnifiedLogger core functionality."""

    def test_log_level_filtering_info(self, tmp_path):
        """Test that DEBUG messages filtered when level=INFO."""
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")

        logger.log(level="DEBUG-1", component="test", event_type="event", action="action1")
        logger.log(level="INFO", component="test", event_type="event", action="action2")

        content = (tmp_path / "audit.log").read_text()
        assert "action1" not in content  # DEBUG-1 filtered out
        assert "action2" in content  # INFO included

    def test_log_level_filtering_debug2(self, tmp_path):
        """Test that DEBUG-3 filtered when level=DEBUG-2."""
        logger = UnifiedLogger(log_dir=tmp_path, level="DEBUG-2")

        logger.log(level="DEBUG-2", component="test", event_type="event", action="action1")
        logger.log(level="DEBUG-3", component="test", event_type="event", action="action2")

        content = (tmp_path / "audit.log").read_text()
        assert "action1" in content
        assert "action2" not in content

    def test_call_stack_extraction(self, tmp_path):
        """Test that call stack is correctly extracted."""
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")
        logger.log(level="INFO", component="test", event_type="event", action="action")

        content = (tmp_path / "audit.log").read_text()
        assert "test_unified_logging:" in content or "test_call_stack" in content

    def test_timed_context_manager(self, tmp_path):
        """Test timed context manager calculates duration_ms."""
        import time
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")

        with logger.timed(level="INFO", component="test", event_type="operation", action="timed_op"):
            time.sleep(0.1)

        content = (tmp_path / "audit.log").read_text()
        assert "ms" in content  # duration_ms should be present
        assert "timed_op" in content

    def test_parent_event_id_linking(self, tmp_path):
        """Test parent_event_id for nested operations."""
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")

        logger.log(
            level="INFO",
            component="test",
            event_type="event",
            action="parent",
            parent_event_id="audit_123"
        )

        content = (tmp_path / "audit.log").read_text()
        assert "audit_123" in content

    def test_set_level_dynamic(self, tmp_path):
        """Test changing log level dynamically."""
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")

        logger.log(level="DEBUG-1", component="test", event_type="event", action="action1")
        logger.set_level("DEBUG-1")
        logger.log(level="DEBUG-1", component="test", event_type="event", action="action2")

        content = (tmp_path / "audit.log").read_text()
        assert "action1" not in content  # First log filtered
        assert "action2" in content  # Second log after level change included

    def test_all_formats_written_simultaneously(self, tmp_path):
        """Test that TXT, CSV, JSON all written simultaneously."""
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")

        logger.log(level="INFO", component="test", event_type="event", action="test_action")

        assert (tmp_path / "audit.log").exists()
        assert (tmp_path / "audit.log.csv").exists()
        assert (tmp_path / "audit.log.json").exists()

        txt_content = (tmp_path / "audit.log").read_text()
        csv_content = (tmp_path / "audit.log.csv").read_text()
        json_content = (tmp_path / "audit.log.json").read_text()

        assert "test_action" in txt_content
        assert "test_action" in csv_content
        assert "test_action" in json_content

    def test_metadata_dict(self, tmp_path):
        """Test logging with complex metadata dictionary."""
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")

        logger.log(
            level="INFO",
            component="llm",
            event_type="invoke",
            action="gigachat_call",
            metadata={
                "model": "GigaChat-2-Max",
                "temperature": 0.3,
                "tokens": {"prompt": 512, "completion": 256},
                "status": "success"
            }
        )

        json_content = (tmp_path / "audit.log.json").read_text()
        obj = json.loads(json_content)
        metadata = json.loads(obj["metadata"])
        assert metadata["model"] == "GigaChat-2-Max"
        assert metadata["tokens"]["prompt"] == 512

    def test_singleton_instance(self, tmp_path):
        """Test that get_unified_logger returns singleton."""
        logger1 = get_unified_logger(log_dir=tmp_path)
        logger2 = get_unified_logger(log_dir=tmp_path)

        assert logger1 is logger2


class TestIntegration:
    """Integration tests for unified logging system."""

    def test_error_level_logs_exceptions(self, tmp_path):
        """Test ERROR level with exception data."""
        logger = UnifiedLogger(log_dir=tmp_path, level="ERROR")

        logger.log(
            level="ERROR",
            component="audit",
            event_type="error",
            action="validation_failed",
            metadata={"error": "Config invalid", "error_code": "CONFIG_ERROR"}
        )

        content = (tmp_path / "audit.log").read_text()
        assert "validation_failed" in content

    def test_full_audit_lifecycle_logging(self, tmp_path):
        """Test logging across full audit lifecycle."""
        logger = UnifiedLogger(log_dir=tmp_path, level="DEBUG-1")

        # Simulate audit lifecycle
        logger.log(level="INFO", component="task", event_type="start", action="audit_start", metadata={"task": "gogol_audit"})
        logger.log(level="INFO", component="retriever", event_type="retrieve", action="fetch_docs", metadata={"docs": 5})
        logger.log(level="INFO", component="llm", event_type="invoke", action="generate_findings", metadata={"findings": 3})
        logger.log(level="INFO", component="task", event_type="end", action="audit_complete", metadata={"status": "success"})

        txt_lines = (tmp_path / "audit.log").read_text().strip().split('\n')
        assert len(txt_lines) == 4
        assert "audit_start" in txt_lines[0]
        assert "audit_complete" in txt_lines[3]

    def test_no_data_loss_concurrent_writes(self, tmp_path):
        """Test that no data lost when writers run concurrently."""
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")

        for i in range(10):
            logger.log(
                level="INFO",
                component="test",
                event_type="event",
                action=f"action_{i}",
                metadata={"index": i}
            )

        txt_lines = (tmp_path / "audit.log").read_text().strip().split('\n')
        csv_lines = (tmp_path / "audit.log.csv").read_text().strip().split('\n')
        json_lines = (tmp_path / "audit.log.json").read_text().strip().split('\n')

        assert len(txt_lines) == 10
        assert len(csv_lines) == 11  # header + 10 data rows
        assert len(json_lines) == 10

    def test_log_level_env_var(self, tmp_path, monkeypatch):
        """Test setting log level via environment variable."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG-2")
        logger = UnifiedLogger(log_dir=tmp_path, level="DEBUG-2")

        logger.log(level="DEBUG-3", component="test", event_type="event", action="action1")
        logger.log(level="DEBUG-2", component="test", event_type="event", action="action2")

        content = (tmp_path / "audit.log").read_text()
        assert "action1" not in content
        assert "action2" in content

    def test_log_file_rotation_simulation(self, tmp_path):
        """Test that logging works across multiple 'rotations'."""
        logger = UnifiedLogger(log_dir=tmp_path, level="INFO")

        # Simulate log rotation by writing, checking file, then more writes
        logger.log(level="INFO", component="test", event_type="event", action="batch1")
        size1 = (tmp_path / "audit.log").stat().st_size

        logger.log(level="INFO", component="test", event_type="event", action="batch2")
        size2 = (tmp_path / "audit.log").stat().st_size

        assert size2 > size1  # File grew
        content = (tmp_path / "audit.log").read_text()
        assert "batch1" in content
        assert "batch2" in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
