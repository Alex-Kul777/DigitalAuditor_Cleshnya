"""Unified logging system with 3 output formats (TXT/CSV/JSON) and 6 detail levels."""

import json
import csv
import sys
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from contextlib import contextmanager
import time
import inspect


@dataclass
class LogEvent:
    """Structured log event."""
    timestamp: str
    level: str
    module: str
    method: str
    line: int
    component: str
    event_type: str
    action: str
    duration_ms: Optional[int] = None
    parent_event_id: Optional[str] = None
    agent: str = "DigitalAuditor"
    system: str = "DigitalAuditor"
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dict for JSON/CSV."""
        d = asdict(self)
        d['metadata'] = json.dumps(d['metadata'] or {}, ensure_ascii=False)
        return d


class ConsoleWriter:
    """Write logs to stdout (console)."""

    def __init__(self):
        self.lock = threading.Lock()

    def write(self, event: LogEvent):
        """Write one line to console (stdout)."""
        metadata_str = json.dumps(event.metadata or {}, ensure_ascii=False) if event.metadata else ""
        duration_str = f" | {event.duration_ms}ms" if event.duration_ms else ""
        # Format: [LEVEL] module:method | component | action | metadata
        msg = f"[{event.level}] {event.module}:{event.method}:{event.line} | {event.component}.{event.event_type} | {event.action}{duration_str}"
        if metadata_str and event.metadata:
            msg += f" | {metadata_str}"
        with self.lock:
            print(msg, file=sys.stdout)
            sys.stdout.flush()


class TxtWriter:
    """Write logs to audit.log in human-readable format."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.lock = threading.Lock()

    def write(self, event: LogEvent):
        """Write one line to TXT log."""
        metadata_str = json.dumps(event.metadata or {}, ensure_ascii=False) if event.metadata else "{}"
        duration_str = f" | {event.duration_ms}ms" if event.duration_ms else ""
        parent_str = f" | parent:{event.parent_event_id}" if event.parent_event_id else ""
        line = (
            f"{event.timestamp} | {event.level} | "
            f"{event.module}:{event.method}:{event.line} | "
            f"{event.component}.{event.event_type} | {event.action}{duration_str}{parent_str} | "
            f"{event.agent} | {metadata_str}"
        )
        with self.lock:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(line + '\n')


class CsvWriter:
    """Write logs to audit.log.csv in tabular format."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.lock = threading.Lock()
        self.headers = [
            'timestamp', 'level', 'module', 'method', 'line', 'component',
            'event_type', 'action', 'duration_ms', 'parent_event_id', 'agent',
            'system', 'metadata'
        ]
        self._init_header()

    def _init_header(self):
        """Write CSV header if file is new."""
        if not self.log_file.exists():
            with self.lock:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.headers)
                    writer.writeheader()

    def write(self, event: LogEvent):
        """Write one row to CSV log."""
        row = event.to_dict()
        with self.lock:
            with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writerow(row)


class JsonWriter:
    """Write logs to audit.log.json in JSONL format (one JSON per line)."""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.lock = threading.Lock()

    def write(self, event: LogEvent):
        """Write one JSON object to JSONL log."""
        json_obj = event.to_dict()
        with self.lock:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(json_obj, ensure_ascii=False) + '\n')


class UnifiedLogger:
    """Unified logging system writing to TXT/CSV/JSON with 6 detail levels."""

    LEVELS = ['ERROR', 'WARNING', 'INFO', 'DEBUG-1', 'DEBUG-2', 'DEBUG-3']
    LEVEL_ORDER = {level: idx for idx, level in enumerate(LEVELS)}

    def __init__(self, log_dir: Path = None, level: str = "INFO"):
        if log_dir is None:
            log_dir = Path("logs")
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_dir / "audit.log"
        self.csv_file = self.log_dir / "audit.log.csv"
        self.json_file = self.log_dir / "audit.log.json"

        self.writers = [
            ConsoleWriter(),
            TxtWriter(self.log_file),
            CsvWriter(self.csv_file),
            JsonWriter(self.json_file),
        ]
        self.set_level(level)
        self.lock = threading.Lock()

    def set_level(self, level: str):
        """Set minimum log level (filters below this)."""
        if level not in self.LEVEL_ORDER:
            print(f"[WARNING] Unknown log level {level}, using INFO", file=sys.stderr)
            level = "INFO"
        self.level = level
        self.level_order = self.LEVEL_ORDER[level]

    def _should_log(self, level: str) -> bool:
        """Check if event should be logged based on level."""
        if level not in self.LEVEL_ORDER:
            return False
        return self.LEVEL_ORDER[level] <= self.level_order

    @staticmethod
    def _get_call_info() -> tuple:
        """Extract module, method, line from call stack (skip UnifiedLogger frames)."""
        frame = inspect.currentframe()
        try:
            # Skip frames: _get_call_info -> log/timed -> caller
            while frame:
                code = frame.f_code
                module_name = code.co_filename.split('/')[-1].replace('.py', '')
                # Skip our own module
                if 'unified_logger' not in code.co_filename:
                    method = code.co_name
                    line = frame.f_lineno
                    return (module_name, method, line)
                frame = frame.f_back
            return ("unknown", "unknown", 0)
        finally:
            del frame

    def log(self,
            level: str,
            component: str,
            event_type: str,
            action: str,
            agent: str = "DigitalAuditor",
            duration_ms: Optional[int] = None,
            parent_event_id: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None):
        """Log a structured event."""
        if not self._should_log(level):
            return

        module, method, line = self._get_call_info()
        timestamp = datetime.now().isoformat(timespec='milliseconds')

        event = LogEvent(
            timestamp=timestamp,
            level=level,
            module=module,
            method=method,
            line=line,
            component=component,
            event_type=event_type,
            action=action,
            duration_ms=duration_ms,
            parent_event_id=parent_event_id,
            agent=agent,
            system="DigitalAuditor",
            metadata=metadata or {}
        )

        with self.lock:
            for writer in self.writers:
                try:
                    writer.write(event)
                except Exception:
                    pass  # Silently fail on write errors

    @contextmanager
    def timed(self,
              level: str,
              component: str,
              event_type: str,
              action: str,
              agent: str = "DigitalAuditor",
              parent_event_id: Optional[str] = None,
              metadata: Optional[Dict[str, Any]] = None):
        """Context manager for timed operations (calculates duration_ms)."""
        start = time.time()
        try:
            yield
        finally:
            duration_ms = int((time.time() - start) * 1000)
            self.log(
                level=level,
                component=component,
                event_type=event_type,
                action=action,
                agent=agent,
                duration_ms=duration_ms,
                parent_event_id=parent_event_id,
                metadata=metadata
            )


# Singleton instance
_unified_logger_instance: Optional[UnifiedLogger] = None


def get_unified_logger(log_dir: Path = None, level: str = "INFO") -> UnifiedLogger:
    """Get or create unified logger singleton."""
    global _unified_logger_instance
    if _unified_logger_instance is None:
        _unified_logger_instance = UnifiedLogger(log_dir, level)
    return _unified_logger_instance


def set_log_level(level: str):
    """Change global log level."""
    logger = get_unified_logger()
    logger.set_level(level)
