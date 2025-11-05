"""Structured logging for GenesisPantheon using loguru."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger as _loguru_logger

# Remove default handler
_loguru_logger.remove()

# Console handler with structured format
_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:"
    "<cyan>{line}</cyan> - <level>{message}</level>"
)

_loguru_logger.add(
    sys.stderr,
    format=_LOG_FORMAT,
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# Re-export as `logger`
logger = _loguru_logger


def configure_file_logging(
    log_path: Optional[Path] = None,
    level: str = "DEBUG",
    rotation: str = "10 MB",
    retention: str = "1 week",
) -> None:
    """Add a rotating file handler to the logger.

    Args:
        log_path: Path to the log file. Defaults to
            ~/.genesis_pantheon/logs/genesis.log
        level: Minimum log level for the file handler.
        rotation: When to rotate the log file.
        retention: How long to keep old log files.
    """
    if log_path is None:
        log_path = (
            Path.home() / ".genesis_pantheon" / "logs" / "genesis.log"
        )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _loguru_logger.add(
        str(log_path),
        format=_LOG_FORMAT,
        level=level,
        rotation=rotation,
        retention=retention,
        backtrace=True,
        diagnose=True,
    )


def set_log_level(level: str) -> None:
    """Dynamically update the console log level.

    Args:
        level: New minimum log level (DEBUG, INFO, WARNING, ERROR).
    """
    _loguru_logger.remove()
    _loguru_logger.add(
        sys.stderr,
        format=_LOG_FORMAT,
        level=level.upper(),
        colorize=True,
        backtrace=True,
        diagnose=True,
    )


__all__ = ["logger", "configure_file_logging", "set_log_level"]
