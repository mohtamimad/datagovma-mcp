import logging

import pytest

from datagovma_mcp.utils.logging_config import (
    configure_logging,
    normalize_log_format,
    normalize_log_level,
    resolve_log_format,
)


def test_normalize_log_level_defaults_when_blank():
    assert normalize_log_level("   ") == "INFO"


def test_normalize_log_level_normalizes_case_and_spaces():
    assert normalize_log_level("  debug ") == "DEBUG"


def test_normalize_log_level_rejects_invalid_value():
    with pytest.raises(ValueError, match="Invalid MCP_LOG_LEVEL"):
        normalize_log_level("verbose")


def test_normalize_log_format_defaults_to_auto_when_blank():
    assert normalize_log_format("   ") == "auto"


def test_normalize_log_format_accepts_plain():
    assert normalize_log_format("plain") == "plain"


def test_normalize_log_format_rejects_invalid_value():
    with pytest.raises(ValueError, match="Invalid MCP_LOG_FORMAT"):
        normalize_log_format("json")


def test_resolve_log_format_auto_prefers_rich_on_tty():
    assert resolve_log_format("auto", rich_available=True, is_tty=True) == "rich"


def test_resolve_log_format_auto_uses_plain_without_tty():
    assert resolve_log_format("auto", rich_available=True, is_tty=False) == "plain"


def test_resolve_log_format_rich_falls_back_to_plain_when_missing():
    assert resolve_log_format("rich", rich_available=False, is_tty=True) == "plain"


def test_configure_logging_uses_env_value(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MCP_LOG_FORMAT", "plain")

    resolved = configure_logging()

    assert resolved == "DEBUG"
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG


def test_configure_logging_rejects_invalid_env_value(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCP_LOG_LEVEL", "nope")

    with pytest.raises(ValueError, match="Invalid MCP_LOG_LEVEL"):
        configure_logging()


def test_configure_logging_rejects_invalid_format_env_value(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCP_LOG_FORMAT", "sparkles")

    with pytest.raises(ValueError, match="Invalid MCP_LOG_FORMAT"):
        configure_logging()
