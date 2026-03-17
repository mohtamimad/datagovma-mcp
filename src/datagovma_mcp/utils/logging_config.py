"""Logging setup helpers for the MCP server."""

from __future__ import annotations

import logging
import os

DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVEL_ENV_VAR = "MCP_LOG_LEVEL"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"


def normalize_log_level(raw_level: str | None) -> str:
    """Normalize and validate a log level string."""

    level_name = (
        DEFAULT_LOG_LEVEL if raw_level is None else raw_level.strip().upper() or DEFAULT_LOG_LEVEL
    )

    if not hasattr(logging, level_name):
        raise ValueError(f"Invalid {LOG_LEVEL_ENV_VAR} value: {raw_level!r}")

    level_value = getattr(logging, level_name)
    if not isinstance(level_value, int):
        raise ValueError(f"Invalid {LOG_LEVEL_ENV_VAR} value: {raw_level!r}")
    return level_name


def configure_logging(log_level: str | None = None) -> str:
    """
    Configure process logging once and return the resolved log level name.

    The value can be provided directly or via ``MCP_LOG_LEVEL``.
    """

    resolved_level = normalize_log_level(log_level or os.getenv(LOG_LEVEL_ENV_VAR))
    level_value = getattr(logging, resolved_level)
    root_logger = logging.getLogger()

    if root_logger.handlers:
        root_logger.setLevel(level_value)
    else:
        logging.basicConfig(level=level_value, format=LOG_FORMAT)

    return resolved_level
