"""Environment-backed server configuration helpers."""

from __future__ import annotations

import os


def get_server_config() -> tuple[str, int]:
    """
    Return MCP host and port from environment variables.

    Supported keys:
    - ``MCP_HOST`` (default ``127.0.0.1``)
    - ``MCP_PORT`` (default ``8000``)
    """

    host = os.getenv("MCP_HOST", "127.0.0.1")
    raw_port = os.getenv("MCP_PORT", "8000")

    try:
        port = int(raw_port)
    except ValueError as exc:  # pragma: no cover - validated by tests
        raise ValueError(f"Invalid MCP_PORT value: {raw_port!r}") from exc

    if not (0 < port < 65536):  # pragma: no cover - validated by tests
        raise ValueError(f"MCP_PORT must be between 1 and 65535, got {port}")

    return host, port
