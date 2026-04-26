"""Logger setup for DigitalAuditor Cleshnya using unified logging system."""

import logging
from pathlib import Path
from typing import Optional

from core.config import LOG_LEVEL, LOG_FILE
from core.unified_logger import get_unified_logger, UnifiedLogger


class LoggerAdapter:
    """Adapter to make UnifiedLogger compatible with logging.Logger interface."""

    def __init__(self, name: str, unified_logger: UnifiedLogger):
        self.name = name
        self.unified = unified_logger
        # Extract component from module name (e.g., "core.llm" -> "llm")
        self.component = name.split('.')[-1] if '.' in name else name

    def debug(self, msg: str, *args, **kwargs):
        """Log at DEBUG-1 level (backward compat)."""
        metadata = {"message": msg % args if args else msg}
        self.unified.log(
            level="DEBUG-1",
            component=self.component,
            event_type="debug",
            action="debug_msg",
            metadata=metadata
        )

    def structured_log(self, event_type: str, action: str, context: dict = None, level: str = "INFO"):
        """Log structured event with custom metadata and context.

        Args:
            event_type: Type of event (e.g., "provider_selection", "fallback_attempt")
            action: Action description (e.g., "gigachat_check", "ollama_fallback")
            context: Dict with context data (merged into metadata)
            level: Log level (INFO, DEBUG-1, DEBUG-2, WARNING, ERROR)
        """
        metadata = context or {}
        self.unified.log(
            level=level,
            component=self.component,
            event_type=event_type,
            action=action,
            metadata=metadata
        )

    def info(self, msg: str, *args, **kwargs):
        """Log at INFO level."""
        metadata = {"message": msg % args if args else msg}
        self.unified.log(
            level="INFO",
            component=self.component,
            event_type="info",
            action="info_msg",
            metadata=metadata
        )

    def warning(self, msg: str, *args, **kwargs):
        """Log at WARNING level."""
        metadata = {"message": msg % args if args else msg}
        self.unified.log(
            level="WARNING",
            component=self.component,
            event_type="warning",
            action="warning_msg",
            metadata=metadata
        )

    def error(self, msg: str, *args, exc_info=False, **kwargs):
        """Log at ERROR level."""
        metadata = {"message": msg % args if args else msg}
        if exc_info:
            import traceback
            metadata["exception"] = traceback.format_exc()
        self.unified.log(
            level="ERROR",
            component=self.component,
            event_type="error",
            action="error_msg",
            metadata=metadata
        )

    def critical(self, msg: str, *args, **kwargs):
        """Log at ERROR level (critical mapped to ERROR)."""
        self.error(msg, *args, **kwargs)

    # Aliases for compatibility
    def warn(self, msg: str, *args, **kwargs):
        """Alias for warning (deprecated)."""
        self.warning(msg, *args, **kwargs)

    def log(self, level: int, msg: str, *args, **kwargs):
        """Log at specified level (numeric)."""
        level_name = logging.getLevelName(level)
        metadata = {"message": msg % args if args else msg}
        self.unified.log(
            level="INFO",  # Default to INFO for numeric levels
            component=self.component,
            event_type="log",
            action="log_msg",
            metadata=metadata
        )

    def setLevel(self, level):
        """Set log level (no-op, uses unified logger's level)."""
        pass

    def addHandler(self, hdlr):
        """Add handler (no-op for unified logger)."""
        pass

    def removeHandler(self, hdlr):
        """Remove handler (no-op for unified logger)."""
        pass


_loggers = {}


def setup_logger(name: str, json_output: bool = False) -> LoggerAdapter:
    """
    Set up logger with unified logging system.

    Args:
        name: Logger name (typically module name or "main.component")
        json_output: Ignored (all output goes to unified logger)

    Returns:
        LoggerAdapter instance (compatible with logging.Logger)
    """
    if name in _loggers:
        return _loggers[name]

    # Ensure logs directory exists
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get or create unified logger
    unified = get_unified_logger(log_dir=log_path.parent, level=LOG_LEVEL)

    # Create adapter for backward compatibility
    adapter = LoggerAdapter(name, unified)
    _loggers[name] = adapter
    return adapter
