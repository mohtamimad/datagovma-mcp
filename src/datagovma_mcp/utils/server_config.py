"""Environment-backed server configuration helpers."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UvicornServerConfig:
    """Resolved HTTP server settings used for Uvicorn startup."""

    host: str
    port: int
    workers: int
    reload: bool
    timeout_keep_alive: int


def _parse_host(raw_value: str) -> str:
    """Parse a host value with trim + blank-to-default behavior."""

    normalized = raw_value.strip()
    return normalized or "127.0.0.1"


def _parse_int(raw_value: str, *, env_var: str) -> int:
    """Parse an integer environment variable value."""

    try:
        return int(raw_value.strip())
    except ValueError as exc:  # pragma: no cover - validated by tests
        logger.error("Invalid %s value: %r", env_var, raw_value)
        raise ValueError(f"Invalid {env_var} value: {raw_value!r}") from exc


def _parse_bool(raw_value: str, *, env_var: str) -> bool:
    """Parse a boolean environment variable value."""

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    logger.error("Invalid %s value: %r", env_var, raw_value)
    raise ValueError(f"Invalid {env_var} value: {raw_value!r}")


def get_server_config() -> tuple[str, int]:
    """
    Return MCP host and port from environment variables.

    Supported keys:
    - ``MCP_HOST`` (default ``127.0.0.1``)
    - ``MCP_PORT`` (default ``8000``)
    """

    raw_host = os.getenv("MCP_HOST", "127.0.0.1")
    raw_port = os.getenv("MCP_PORT", "8000")
    host = _parse_host(raw_host)
    logger.debug("Resolving server config from environment host=%s port=%s", host, raw_port)

    port = _parse_int(raw_port, env_var="MCP_PORT")

    if not (0 < port < 65536):  # pragma: no cover - validated by tests
        logger.error("MCP_PORT must be between 1 and 65535, got %s", port)
        raise ValueError(f"MCP_PORT must be between 1 and 65535, got {port}")

    logger.debug("Server config resolved host=%s port=%s", host, port)
    return host, port


def get_uvicorn_server_config() -> UvicornServerConfig:
    """
    Return resolved Uvicorn startup settings from environment variables.

    Supported keys:
    - ``MCP_HOST`` (default ``127.0.0.1``)
    - ``MCP_PORT`` (default ``8000``)
    - ``MCP_WORKERS`` (default ``1``)
    - ``MCP_RELOAD`` (default ``false``)
    - ``MCP_TIMEOUT_KEEP_ALIVE`` (default ``5``)
    """

    host, port = get_server_config()
    raw_workers = os.getenv("MCP_WORKERS", "1")
    raw_reload = os.getenv("MCP_RELOAD", "false")
    raw_timeout_keep_alive = os.getenv("MCP_TIMEOUT_KEEP_ALIVE", "5")
    logger.debug(
        "Resolving uvicorn config workers=%s reload=%s timeout_keep_alive=%s",
        raw_workers,
        raw_reload,
        raw_timeout_keep_alive,
    )

    workers = _parse_int(raw_workers, env_var="MCP_WORKERS")
    if workers < 1:
        logger.error("MCP_WORKERS must be >= 1, got %s", workers)
        raise ValueError(f"MCP_WORKERS must be >= 1, got {workers}")

    reload = _parse_bool(raw_reload, env_var="MCP_RELOAD")
    if reload and workers != 1:
        logger.error("Invalid server config: MCP_RELOAD=true requires MCP_WORKERS=1")
        raise ValueError("MCP_RELOAD=true requires MCP_WORKERS=1")

    timeout_keep_alive = _parse_int(raw_timeout_keep_alive, env_var="MCP_TIMEOUT_KEEP_ALIVE")
    if timeout_keep_alive < 1:
        logger.error("MCP_TIMEOUT_KEEP_ALIVE must be >= 1, got %s", timeout_keep_alive)
        raise ValueError(f"MCP_TIMEOUT_KEEP_ALIVE must be >= 1, got {timeout_keep_alive}")

    logger.debug(
        "Resolved uvicorn config host=%s port=%s workers=%s reload=%s timeout_keep_alive=%s",
        host,
        port,
        workers,
        reload,
        timeout_keep_alive,
    )
    return UvicornServerConfig(
        host=host,
        port=port,
        workers=workers,
        reload=reload,
        timeout_keep_alive=timeout_keep_alive,
    )
