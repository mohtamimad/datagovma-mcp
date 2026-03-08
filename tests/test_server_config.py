from utils.server_config import get_server_config


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

    try:
        get_server_config()
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Invalid MCP_PORT" in str(exc)
