"""
Advanced logging utilities for DigitalAuditor Cleshnya.

Provides structured logging with contextual information, JSON output,
and process mining capabilities.
"""
import logging
import json
import time
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, Dict, Any


class ContextualFormatter(logging.Formatter):
    """
    Formatter that includes module.class.method information.

    Format: timestamp | LEVEL | module.Class.method | message
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with contextual information."""
        # Build class.method info if available
        func_info = record.funcName
        if record.name and record.name != "root":
            func_info = f"{record.name}.{record.funcName}"

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Build the log message
        log_msg = f"{timestamp} | {record.levelname:8s} | {func_info:40s} | {record.getMessage()}"

        # Add exception info if present
        if record.exc_info:
            log_msg += "\n" + self.formatException(record.exc_info)

        return log_msg


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs structured JSON logs.

    Useful for process mining and automated log analysis.
    Includes: timestamp, level, module, message, stage, metrics, line number.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "lineno": record.lineno,
        }

        # Add stage if available (from LogContext)
        if hasattr(record, "stage"):
            log_data["stage"] = record.stage

        # Add duration if available (from LogContext)
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        # Add metrics if available
        if hasattr(record, "metrics"):
            log_data["metrics"] = record.metrics

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class DualLogHandler:
    """
    Manages dual-stream logging: text to console, JSON to file.

    Simplifies setup of logging configuration for both human-readable
    and machine-readable outputs.
    """

    @staticmethod
    def setup(
        logger: logging.Logger,
        log_file: str,
        json_file: Optional[str] = None,
        level: str = "INFO",
    ) -> None:
        """
        Configure logger with dual handlers.

        Args:
            logger: Logger instance to configure
            log_file: Path to text log file
            json_file: Path to JSON log file (optional)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)

        # Create file paths
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Console handler with ContextualFormatter (text)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ContextualFormatter())
        logger.addHandler(console_handler)

        # Text file handler
        text_file_handler = logging.FileHandler(log_file, encoding="utf-8")
        text_file_handler.setLevel(log_level)
        text_file_handler.setFormatter(ContextualFormatter())
        logger.addHandler(text_file_handler)

        # JSON file handler (optional)
        if json_file:
            json_path = Path(json_file)
            json_path.parent.mkdir(parents=True, exist_ok=True)
            json_file_handler = logging.FileHandler(json_file, encoding="utf-8")
            json_file_handler.setLevel(log_level)
            json_file_handler.setFormatter(JSONFormatter())
            logger.addHandler(json_file_handler)

        # Prevent propagation to root logger
        logger.propagate = False


class LogContext:
    """
    Context manager for stage-based logging with duration tracking.

    Logs [STAGE START] at entry and [STAGE END] with duration at exit.
    """

    def __init__(self, logger: logging.Logger, stage_name: str, **metrics):
        """
        Initialize LogContext.

        Args:
            logger: Logger instance
            stage_name: Name of the audit stage
            **metrics: Additional metrics to log
        """
        self.logger = logger
        self.stage_name = stage_name
        self.metrics = metrics
        self.start_time = None

    def __enter__(self):
        """Log stage start and record time."""
        self.start_time = time.time()
        self.logger.info(f"[STAGE START] {self.stage_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log stage end with duration."""
        duration_ms = int((time.time() - self.start_time) * 1000)

        if exc_type is None:
            self.logger.info(
                f"[STAGE END] {self.stage_name} - {duration_ms}ms",
                extra={"duration_ms": duration_ms, "stage": self.stage_name},
            )
        else:
            self.logger.error(
                f"[STAGE ERROR] {self.stage_name} - {duration_ms}ms - {exc_type.__name__}",
                extra={"duration_ms": duration_ms, "stage": self.stage_name},
                exc_info=(exc_type, exc_val, exc_tb),
            )
        return False


class PipelineTimer:
    """
    Utility for tracking execution time of pipeline stages.

    Accumulates timing data for reporting and optimization analysis.
    """

    def __init__(self):
        """Initialize PipelineTimer."""
        self.stages: Dict[str, list] = {}

    def record(self, stage_name: str, duration_ms: float) -> None:
        """Record stage execution time."""
        if stage_name not in self.stages:
            self.stages[stage_name] = []
        self.stages[stage_name].append(duration_ms)

    def get_stats(self, stage_name: str) -> Dict[str, float]:
        """Get execution stats for a stage."""
        if stage_name not in self.stages or not self.stages[stage_name]:
            return {}

        times = self.stages[stage_name]
        return {
            "count": len(times),
            "total_ms": sum(times),
            "avg_ms": sum(times) / len(times),
            "min_ms": min(times),
            "max_ms": max(times),
        }

    def report(self) -> str:
        """Generate timing report."""
        report_lines = ["Pipeline Timing Report:", "=" * 50]
        for stage_name, times in self.stages.items():
            stats = self.get_stats(stage_name)
            report_lines.append(
                f"{stage_name:40s} | "
                f"count={stats['count']:3d} | "
                f"avg={stats['avg_ms']:8.1f}ms | "
                f"total={stats['total_ms']:10.0f}ms"
            )
        return "\n".join(report_lines)


class MemoryTracker:
    """
    Utility for tracking memory usage during audit.

    Simple wrapper around psutil for memory monitoring.
    """

    def __init__(self, logger: logging.Logger):
        """Initialize MemoryTracker."""
        self.logger = logger
        try:
            import psutil
            self.psutil = psutil
            self.process = psutil.Process()
        except ImportError:
            self.logger.warning("psutil not installed. Memory tracking disabled.")
            self.psutil = None

    def log_memory_usage(self, stage_name: str = "") -> None:
        """Log current memory usage."""
        if self.psutil is None:
            return

        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()

        self.logger.info(
            f"Memory usage {stage_name}: "
            f"{memory_info.rss / 1024 / 1024:.1f}MB ({memory_percent:.1f}%)"
        )


class BottleneckAnalyzer:
    """
    Analyze logging data to identify performance bottlenecks.

    Works with PipelineTimer data to find slowest stages.
    """

    def __init__(self, timer: PipelineTimer):
        """Initialize BottleneckAnalyzer."""
        self.timer = timer

    def find_bottlenecks(self, top_n: int = 5) -> list:
        """
        Find slowest stages.

        Args:
            top_n: Number of top slowest stages to return

        Returns:
            List of (stage_name, avg_time_ms) tuples sorted by time desc
        """
        stages_by_avg = [
            (name, self.timer.get_stats(name)["avg_ms"])
            for name in self.timer.stages.keys()
        ]
        stages_by_avg.sort(key=lambda x: x[1], reverse=True)
        return stages_by_avg[:top_n]

    def report(self) -> str:
        """Generate bottleneck report."""
        bottlenecks = self.find_bottlenecks()
        report_lines = ["Performance Bottleneck Analysis:", "=" * 50]
        for i, (stage_name, avg_ms) in enumerate(bottlenecks, 1):
            report_lines.append(f"{i}. {stage_name:40s} {avg_ms:8.1f}ms")
        return "\n".join(report_lines)


class MetricsExporter:
    """
    Export audit metrics in various formats.

    Supports CSV, JSON, and plain text export.
    """

    def __init__(self, timer: PipelineTimer):
        """Initialize MetricsExporter."""
        self.timer = timer

    def export_json(self, output_file: str) -> None:
        """Export metrics as JSON."""
        data = {
            stage: self.timer.get_stats(stage)
            for stage in self.timer.stages.keys()
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def export_csv(self, output_file: str) -> None:
        """Export metrics as CSV."""
        lines = ["stage_name,count,total_ms,avg_ms,min_ms,max_ms"]
        for stage_name in self.timer.stages.keys():
            stats = self.timer.get_stats(stage_name)
            lines.append(
                f"{stage_name},{stats['count']},{stats['total_ms']:.0f},"
                f"{stats['avg_ms']:.1f},{stats['min_ms']:.1f},{stats['max_ms']:.1f}"
            )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
