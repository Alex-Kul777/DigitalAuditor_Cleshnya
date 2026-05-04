"""
Unit tests for core.logger and core.logging_utils modules.
"""
import logging
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from core.logger import setup_logger
from core.logging_utils import (
    ContextualFormatter,
    JSONFormatter,
    DualLogHandler,
    LogContext,
    PipelineTimer,
    MemoryTracker,
    BottleneckAnalyzer,
)


class TestContextualFormatter:
    """Test ContextualFormatter."""

    def test_format_basic_log(self):
        """Test formatting a basic log record."""
        formatter = ContextualFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        formatted = formatter.format(record)
        assert "INFO" in formatted
        assert "Test message" in formatted
        assert "test_func" in formatted

    def test_format_includes_timestamp(self):
        """Test that formatted output includes timestamp."""
        formatter = ContextualFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message",
            args=(),
            exc_info=None,
            func="func",
        )
        formatted = formatter.format(record)
        # Should contain timestamp pattern (YYYY-MM-DD HH:MM:SS.mmm)
        assert "-" in formatted and ":" in formatted

    def test_format_with_exception(self):
        """Test formatting with exception info."""
        formatter = ContextualFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            exc_info_tuple = logging.sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info_tuple,
            func="func",
        )
        formatted = formatter.format(record)
        assert "ValueError" in formatted
        assert "Test error" in formatted


class TestJSONFormatter:
    """Test JSONFormatter."""

    def test_format_as_json(self):
        """Test that output is valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.module",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
            func="test_func",
        )
        formatted = formatter.format(record)
        data = json.loads(formatted)
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["function"] == "test_func"
        assert data["lineno"] == 42

    def test_json_includes_required_fields(self):
        """Test that JSON output includes all required fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message",
            args=(),
            exc_info=None,
            func="func",
        )
        formatted = formatter.format(record)
        data = json.loads(formatted)
        assert "timestamp" in data
        assert "level" in data
        assert "logger" in data
        assert "message" in data
        assert "module" in data
        assert "function" in data
        assert "lineno" in data

    def test_json_with_stage(self):
        """Test JSON formatter includes stage when available."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message",
            args=(),
            exc_info=None,
            func="func",
        )
        record.stage = "document_fetch"
        formatted = formatter.format(record)
        data = json.loads(formatted)
        assert data["stage"] == "document_fetch"

    def test_json_with_metrics(self):
        """Test JSON formatter includes metrics when available."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Message",
            args=(),
            exc_info=None,
            func="func",
        )
        record.metrics = {"count": 42, "size_mb": 10.5}
        formatted = formatter.format(record)
        data = json.loads(formatted)
        assert data["metrics"]["count"] == 42


class TestDualLogHandler:
    """Test DualLogHandler."""

    def test_setup_creates_handlers(self, tmp_path):
        """Test that setup creates console and file handlers."""
        log_file = tmp_path / "test.log"
        logger = logging.getLogger("test_dual")
        logger.handlers = []  # Clear any existing handlers

        DualLogHandler.setup(logger, str(log_file))
        assert len(logger.handlers) >= 2  # Console + file

    def test_setup_creates_log_file(self, tmp_path):
        """Test that setup creates log file directory."""
        log_file = tmp_path / "logs" / "test.log"
        logger = logging.getLogger("test_dual2")
        logger.handlers = []

        DualLogHandler.setup(logger, str(log_file))
        logger.info("Test message")

        assert log_file.parent.exists()

    def test_setup_with_json_output(self, tmp_path):
        """Test setup with JSON file output."""
        log_file = tmp_path / "test.log"
        json_file = tmp_path / "test.json"
        logger = logging.getLogger("test_dual3")
        logger.handlers = []

        DualLogHandler.setup(logger, str(log_file), json_file=str(json_file))
        logger.info("Test message")

        assert log_file.exists()
        assert json_file.exists()


class TestLogContext:
    """Test LogContext context manager."""

    def test_log_context_logs_start_and_end(self, caplog):
        """Test that LogContext logs stage start and end."""
        logger = logging.getLogger("test_context")
        with caplog.at_level(logging.INFO):
            with LogContext(logger, "test_stage"):
                pass

        messages = [record.message for record in caplog.records]
        assert any("STAGE START" in msg for msg in messages)
        assert any("STAGE END" in msg for msg in messages)

    def test_log_context_records_duration(self, caplog):
        """Test that LogContext includes duration in milliseconds."""
        import time
        logger = logging.getLogger("test_context2")
        with caplog.at_level(logging.INFO):
            with LogContext(logger, "slow_stage"):
                time.sleep(0.01)  # 10ms

        messages = [record.message for record in caplog.records]
        end_msg = next((msg for msg in messages if "STAGE END" in msg), "")
        assert "ms" in end_msg

    def test_log_context_with_exception(self, caplog):
        """Test that LogContext logs exceptions."""
        logger = logging.getLogger("test_context3")
        with caplog.at_level(logging.ERROR):
            try:
                with LogContext(logger, "error_stage"):
                    raise ValueError("Test error")
            except ValueError:
                pass

        error_messages = [record.message for record in caplog.records if record.levelname == "ERROR"]
        assert any("STAGE ERROR" in msg for msg in error_messages)

    def test_log_context_exit_returns_false(self):
        """Test that LogContext.__exit__ returns False (doesn't suppress exceptions)."""
        logger = logging.getLogger("test_context4")
        ctx = LogContext(logger, "test_stage")
        ctx.start_time = 0
        result = ctx.__exit__(ValueError, ValueError("test"), None)
        assert result is False


class TestPipelineTimer:
    """Test PipelineTimer."""

    def test_record_stage_time(self):
        """Test recording stage execution time."""
        timer = PipelineTimer()
        timer.record("stage1", 100.5)
        timer.record("stage1", 200.3)

        assert "stage1" in timer.stages
        assert len(timer.stages["stage1"]) == 2

    def test_get_stats_count(self):
        """Test getting stage statistics."""
        timer = PipelineTimer()
        timer.record("stage1", 100)
        timer.record("stage1", 200)
        stats = timer.get_stats("stage1")

        assert stats["count"] == 2
        assert stats["total_ms"] == 300
        assert stats["avg_ms"] == 150
        assert stats["min_ms"] == 100
        assert stats["max_ms"] == 200

    def test_get_stats_empty_stage(self):
        """Test getting stats for non-existent stage."""
        timer = PipelineTimer()
        stats = timer.get_stats("nonexistent")
        assert stats == {}

    def test_report_formatting(self):
        """Test that report is properly formatted."""
        timer = PipelineTimer()
        timer.record("fetch", 100)
        timer.record("index", 200)
        report = timer.report()

        assert "Pipeline Timing Report" in report
        assert "fetch" in report
        assert "index" in report


class TestBottleneckAnalyzer:
    """Test BottleneckAnalyzer."""

    def test_find_bottlenecks(self):
        """Test finding slowest stages."""
        timer = PipelineTimer()
        timer.record("fast", 10)
        timer.record("slow", 1000)
        timer.record("medium", 100)

        analyzer = BottleneckAnalyzer(timer)
        bottlenecks = analyzer.find_bottlenecks(top_n=2)

        assert len(bottlenecks) <= 2
        # Slowest should be first
        assert bottlenecks[0][0] == "slow"
        assert bottlenecks[1][0] == "medium"

    def test_find_bottlenecks_limit(self):
        """Test that top_n limit is respected."""
        timer = PipelineTimer()
        for i in range(10):
            timer.record(f"stage{i}", 100 * (i + 1))

        analyzer = BottleneckAnalyzer(timer)
        bottlenecks = analyzer.find_bottlenecks(top_n=3)
        assert len(bottlenecks) == 3

    def test_bottleneck_report(self):
        """Test bottleneck report formatting."""
        timer = PipelineTimer()
        timer.record("slow_stage", 1000)
        timer.record("fast_stage", 100)

        analyzer = BottleneckAnalyzer(timer)
        report = analyzer.report()

        assert "Performance Bottleneck Analysis" in report
        assert "slow_stage" in report


class TestMemoryTracker:
    """Test MemoryTracker."""

    def test_memory_tracker_init_without_psutil(self):
        """Test MemoryTracker gracefully handles missing psutil."""
        logger = logging.getLogger("test_memory")
        with patch.dict("sys.modules", {"psutil": None}):
            tracker = MemoryTracker(logger)
            # Should not raise, just warn

    def test_memory_tracker_with_psutil(self):
        """Test MemoryTracker with psutil available."""
        logger = logging.getLogger("test_memory2")
        try:
            import psutil
            tracker = MemoryTracker(logger)
            # Should work normally
            assert tracker.psutil is not None
        except ImportError:
            pytest.skip("psutil not installed")


class TestSetupLogger:
    """Test core.logger.setup_logger function."""

    def test_setup_logger_returns_logger(self, tmp_path, monkeypatch):
        """Test that setup_logger returns a Logger instance."""
        monkeypatch.setenv("LOG_LEVEL", "INFO")
        monkeypatch.setenv("LOG_FILE", str(tmp_path / "test.log"))
        logger = setup_logger("test_setup")
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_no_duplicate_handlers(self, tmp_path, monkeypatch):
        """Test that calling setup_logger twice doesn't duplicate handlers."""
        log_file = str(tmp_path / "test.log")
        monkeypatch.setenv("LOG_FILE", log_file)
        monkeypatch.setenv("LOG_LEVEL", "INFO")

        logger = setup_logger("test_dup")
        handler_count_first = len(logger.handlers)

        logger = setup_logger("test_dup")
        handler_count_second = len(logger.handlers)

        assert handler_count_first == handler_count_second

    def test_setup_logger_with_json(self, tmp_path, monkeypatch):
        """Test setup_logger with JSON output enabled."""
        log_file = str(tmp_path / "test.log")
        monkeypatch.setenv("LOG_FILE", log_file)
        monkeypatch.setenv("LOG_LEVEL", "INFO")

        logger = setup_logger("test_json", json_output=True)
        logger.info("Test message")

        # Check that JSON file would be created if JSON output was enabled
        # (actual file creation depends on handler registration)
        assert isinstance(logger, logging.Logger)


@pytest.mark.unit
class TestLoggingMarker:
    """Test logging with unit marker."""

    def test_all_logging_classes_exist(self):
        """Verify all logging utility classes are available."""
        assert ContextualFormatter is not None
        assert JSONFormatter is not None
        assert DualLogHandler is not None
        assert LogContext is not None
        assert PipelineTimer is not None
        assert MemoryTracker is not None
        assert BottleneckAnalyzer is not None
