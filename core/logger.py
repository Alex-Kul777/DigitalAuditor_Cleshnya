"""
Logger setup for DigitalAuditor Cleshnya.

Uses DualLogHandler for simultaneous text and JSON logging.
"""
import logging
from pathlib import Path

from core.config import LOG_LEVEL, LOG_FILE
from core.logging_utils import DualLogHandler


def setup_logger(name: str, json_output: bool = False) -> logging.Logger:
    """
    Set up logger with contextual formatting.

    Args:
        name: Logger name (typically module name or "main.component")
        json_output: Enable JSON file output for process mining

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Skip reconfiguration if already configured
    if logger.handlers:
        return logger

    # Ensure logs directory exists
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Set up dual handlers (text + optional JSON)
    json_file = None
    if json_output:
        json_file = str(log_path.parent / "audit.json")

    DualLogHandler.setup(
        logger=logger,
        log_file=LOG_FILE,
        json_file=json_file,
        level=LOG_LEVEL,
    )

    return logger
