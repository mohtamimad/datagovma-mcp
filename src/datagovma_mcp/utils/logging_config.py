"""Logging setup helpers for the MCP server."""

from __future__ import annotations

import logging
import os
import sys
from collections.abc import Collection

DEFAULT_LOG_LEVEL = "INFO"
LOG_LEVEL_ENV_VAR = "MCP_LOG_LEVEL"
DEFAULT_LOG_FORMAT = "auto"
LOG_FORMAT_ENV_VAR = "MCP_LOG_FORMAT"
PLAIN_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"
RICH_MESSAGE_FORMAT = "%(message)s"
_VALID_LOG_FORMATS = {"auto", "plain", "rich"}
logger = logging.getLogger(__name__)


def _normalize_with_default(raw_value: str, *, default: str) -> str:
    """Normalize string settings with blank-to-default behavior."""

    normalized = raw_value.strip()
    return normalized or default


def _validate_choice(
    value: str,
    *,
    allowed: Collection[str],
    env_var: str,
    raw_value: str,
) -> str:
    """Validate a normalized value against an allowed choice list."""

    if value not in allowed:
        raise ValueError(f"Invalid {env_var} value: {raw_value!r}")
    return value


def normalize_log_format(raw_format: str) -> str:
    """Normalize and validate a log output format option."""

    format_name = _normalize_with_default(raw_format, default=DEFAULT_LOG_FORMAT).lower()
    return _validate_choice(
        format_name,
        allowed=_VALID_LOG_FORMATS,
        env_var=LOG_FORMAT_ENV_VAR,
        raw_value=raw_format,
    )


def resolve_log_format(
    requested_format: str,
    *,
    rich_available: bool,
    is_tty: bool,
) -> str:
    """Resolve a concrete output format (``plain`` or ``rich``)."""

    if requested_format == "plain":
        return "plain"
    if requested_format == "rich":
        return "rich" if rich_available else "plain"
    return "rich" if rich_available and is_tty else "plain"


def _is_tty_stderr() -> bool:
    """Return whether stderr is attached to a TTY."""

    return bool(getattr(sys.stderr, "isatty", lambda: False)())


def _create_rich_handler() -> logging.Handler | None:
    """Create a Rich handler when Rich is installed."""

    try:
        from rich.logging import RichHandler
    except ImportError:
        return None

    handler = RichHandler(show_path=False, rich_tracebacks=True, markup=False)
    handler.setFormatter(logging.Formatter(RICH_MESSAGE_FORMAT))
    return handler


def normalize_log_level(raw_level: str) -> str:
    """Normalize and validate a log level string."""

    level_name = _normalize_with_default(raw_level, default=DEFAULT_LOG_LEVEL).upper()
    return _validate_choice(
        level_name,
        allowed=logging.getLevelNamesMapping().keys(),
        env_var=LOG_LEVEL_ENV_VAR,
        raw_value=raw_level,
    )


def _set_root_and_handler_levels(root_logger: logging.Logger, level_value: int) -> None:
    """Apply a level to the root logger and any existing handlers."""

    root_logger.setLevel(level_value)
    for handler in root_logger.handlers:
        handler.setLevel(level_value)


def configure_uvicorn_logging() -> None:
    """Align Uvicorn loggers with the root logging configuration."""

    import uvicorn.config as uvicorn_config

    loggers_config = uvicorn_config.LOGGING_CONFIG.setdefault("loggers", {})
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger_config = loggers_config.setdefault(logger_name, {})
        logger_config["handlers"] = []
        logger_config["propagate"] = True

    # Access logs are noisy for local MCP traffic; keep warnings/errors only.
    loggers_config["uvicorn.access"]["level"] = "WARNING"

    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True
        uvicorn_logger.setLevel(logging.NOTSET)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logger.debug("Uvicorn loggers and LOGGING_CONFIG aligned with root handlers")


def configure_logging(log_level: str | None = None, log_format: str | None = None) -> str:
    """
    Configure process logging once and return the resolved log level name.

    Values can be provided directly or via:
    - ``MCP_LOG_LEVEL``
    - ``MCP_LOG_FORMAT`` (``auto``, ``plain``, ``rich``)
    """

    env_log_level = os.getenv(LOG_LEVEL_ENV_VAR, DEFAULT_LOG_LEVEL)
    env_log_format = os.getenv(LOG_FORMAT_ENV_VAR, DEFAULT_LOG_FORMAT)
    resolved_level = normalize_log_level(log_level if log_level is not None else env_log_level)
    requested_format = normalize_log_format(
        log_format if log_format is not None else env_log_format
    )

    rich_handler = _create_rich_handler() if requested_format != "plain" else None
    resolved_format = resolve_log_format(
        requested_format,
        rich_available=rich_handler is not None,
        is_tty=_is_tty_stderr() if requested_format == "auto" else False,
    )

    level_value = getattr(logging, resolved_level)
    root_logger = logging.getLogger()

    if root_logger.handlers:
        _set_root_and_handler_levels(root_logger, level_value)
    elif resolved_format == "rich" and rich_handler is not None:
        rich_handler.setLevel(level_value)
        logging.basicConfig(
            level=level_value,
            handlers=[rich_handler],
            format=RICH_MESSAGE_FORMAT,
        )
    else:
        logging.basicConfig(level=level_value, format=PLAIN_LOG_FORMAT)

    if requested_format == "rich" and resolved_format == "plain":
        logger.warning("Requested rich logging but Rich is unavailable; falling back to plain logs")

    return resolved_level
