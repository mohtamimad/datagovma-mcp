import logging

import pytest

from datagovma_mcp.utils.logging_config import configure_logging, normalize_log_level


def test_normalize_log_level_defaults_to_info():
    assert normalize_log_level(None) == "INFO"


def test_normalize_log_level_defaults_when_blank():
    assert normalize_log_level("   ") == "INFO"


def test_normalize_log_level_normalizes_case_and_spaces():
    assert normalize_log_level("  debug ") == "DEBUG"


def test_normalize_log_level_rejects_invalid_value():
    with pytest.raises(ValueError, match="Invalid MCP_LOG_LEVEL"):
        normalize_log_level("verbose")


def test_configure_logging_uses_env_value(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")

    resolved = configure_logging()

    assert resolved == "DEBUG"
    assert logging.getLogger().getEffectiveLevel() == logging.DEBUG


def test_configure_logging_rejects_invalid_env_value(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MCP_LOG_LEVEL", "nope")

    with pytest.raises(ValueError, match="Invalid MCP_LOG_LEVEL"):
        configure_logging()
