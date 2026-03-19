import pytest

from datagovma_mcp.utils.server_config import (
    UvicornServerConfig,
    get_server_config,
    get_uvicorn_server_config,
)


def test_get_server_config_defaults(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)

    host, port = get_server_config()
    assert host == "127.0.0.1"
    assert port == 8000


def test_get_server_config_reads_env_values(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9001")

    host, port = get_server_config()
    assert host == "0.0.0.0"
    assert port == 9001


def test_get_server_config_rejects_invalid_port(monkeypatch):
    monkeypatch.setenv("MCP_PORT", "not-a-number")

    with pytest.raises(ValueError, match="Invalid MCP_PORT"):
        get_server_config()


def test_get_uvicorn_server_config_defaults(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.delenv("MCP_WORKERS", raising=False)
    monkeypatch.delenv("MCP_RELOAD", raising=False)
    monkeypatch.delenv("MCP_TIMEOUT_KEEP_ALIVE", raising=False)

    config = get_uvicorn_server_config()
    assert config == UvicornServerConfig(
        host="127.0.0.1",
        port=8000,
        workers=1,
        reload=False,
        timeout_keep_alive=5,
    )


def test_get_uvicorn_server_config_reads_env_values(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9001")
    monkeypatch.setenv("MCP_WORKERS", "4")
    monkeypatch.setenv("MCP_RELOAD", "false")
    monkeypatch.setenv("MCP_TIMEOUT_KEEP_ALIVE", "20")

    config = get_uvicorn_server_config()
    assert config == UvicornServerConfig(
        host="0.0.0.0",
        port=9001,
        workers=4,
        reload=False,
        timeout_keep_alive=20,
    )


def test_get_uvicorn_server_config_rejects_invalid_workers(monkeypatch):
    monkeypatch.setenv("MCP_WORKERS", "0")

    with pytest.raises(ValueError, match="MCP_WORKERS must be >= 1"):
        get_uvicorn_server_config()


def test_get_uvicorn_server_config_rejects_invalid_reload(monkeypatch):
    monkeypatch.setenv("MCP_RELOAD", "maybe")

    with pytest.raises(ValueError, match="Invalid MCP_RELOAD"):
        get_uvicorn_server_config()


def test_get_uvicorn_server_config_rejects_reload_with_multiple_workers(monkeypatch):
    monkeypatch.setenv("MCP_WORKERS", "2")
    monkeypatch.setenv("MCP_RELOAD", "true")

    with pytest.raises(ValueError, match="MCP_RELOAD=true requires MCP_WORKERS=1"):
        get_uvicorn_server_config()
