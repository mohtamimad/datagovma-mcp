import asyncio

from datagovma_mcp import main
from datagovma_mcp.utils.server_config import UvicornServerConfig


def _run_asgi_http_request(app, *, path: str, method: str = "GET") -> list[dict]:
    messages: list[dict] = []
    request_consumed = False

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
    }

    async def _receive():
        nonlocal request_consumed
        if request_consumed:
            return {"type": "http.disconnect"}
        request_consumed = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def _send(message: dict) -> None:
        messages.append(message)

    asyncio.run(app(scope, _receive, _send))
    return messages


def test_create_http_app_injects_truststore_and_serves_healthz(monkeypatch):
    called = {"inject": False, "create": False, "mcp_app_called": False}

    def _fake_inject() -> None:
        called["inject"] = True

    async def _fake_mcp_app(_scope, _receive, _send) -> None:
        called["mcp_app_called"] = True
        await _send({"type": "http.response.start", "status": 204, "headers": []})
        await _send({"type": "http.response.body", "body": b"", "more_body": False})

    class _FakeServer:
        def streamable_http_app(self):
            return _fake_mcp_app

    def _fake_create_server():
        called["create"] = True
        return _FakeServer()

    monkeypatch.setattr("datagovma_mcp.main.truststore.inject_into_ssl", _fake_inject)
    monkeypatch.setattr("datagovma_mcp.main.create_server", _fake_create_server)

    app = main.create_http_app()
    messages = _run_asgi_http_request(app, path="/healthz")

    assert callable(app)
    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 200
    assert messages[1]["type"] == "http.response.body"
    assert messages[1]["body"] == b"ok"
    assert called["inject"] is True
    assert called["create"] is True
    assert called["mcp_app_called"] is False


def test_create_http_app_routes_non_health_requests_to_mcp_app(monkeypatch):
    called = {"mcp_app_called": False}

    async def _fake_mcp_app(_scope, _receive, _send) -> None:
        called["mcp_app_called"] = True
        await _send({"type": "http.response.start", "status": 204, "headers": []})
        await _send({"type": "http.response.body", "body": b"", "more_body": False})

    class _FakeServer:
        def streamable_http_app(self):
            return _fake_mcp_app

    monkeypatch.setattr("datagovma_mcp.main.truststore.inject_into_ssl", lambda: None)
    monkeypatch.setattr("datagovma_mcp.main.create_server", lambda: _FakeServer())

    app = main.create_http_app()
    messages = _run_asgi_http_request(app, path="/mcp")

    assert messages[0]["type"] == "http.response.start"
    assert messages[0]["status"] == 204
    assert called["mcp_app_called"] is True


def test_main_runs_uvicorn_factory(monkeypatch):
    called = {
        "configure": False,
        "uvicorn_configure": False,
        "resolve_server_config": False,
        "uvicorn_run_args": None,
        "uvicorn_run_kwargs": None,
    }

    def _fake_configure_logging() -> str:
        called["configure"] = True
        return "DEBUG"

    def _fake_configure_uvicorn_logging() -> None:
        called["uvicorn_configure"] = True

    def _fake_get_uvicorn_server_config() -> UvicornServerConfig:
        called["resolve_server_config"] = True
        return UvicornServerConfig(
            host="0.0.0.0",
            port=9001,
            workers=2,
            reload=False,
            timeout_keep_alive=15,
        )

    def _fake_uvicorn_run(*args, **kwargs) -> None:
        called["uvicorn_run_args"] = args
        called["uvicorn_run_kwargs"] = kwargs

    monkeypatch.setattr("datagovma_mcp.main.configure_logging", _fake_configure_logging)
    monkeypatch.setattr(
        "datagovma_mcp.main.configure_uvicorn_logging",
        _fake_configure_uvicorn_logging,
    )
    monkeypatch.setattr(
        "datagovma_mcp.main.get_uvicorn_server_config",
        _fake_get_uvicorn_server_config,
    )
    monkeypatch.setattr("datagovma_mcp.main.uvicorn.run", _fake_uvicorn_run)

    main.main()

    assert called["configure"] is True
    assert called["uvicorn_configure"] is True
    assert called["resolve_server_config"] is True
    assert called["uvicorn_run_args"] == ("datagovma_mcp.main:create_http_app",)
    assert called["uvicorn_run_kwargs"] == {
        "factory": True,
        "host": "0.0.0.0",
        "port": 9001,
        "workers": 2,
        "reload": False,
        "timeout_keep_alive": 15,
        "log_level": "debug",
    }


def test_main_handles_keyboard_interrupt(monkeypatch):
    called = {"configure": False, "uvicorn_configure": False}

    def _fake_configure_logging() -> str:
        called["configure"] = True
        return "INFO"

    def _fake_configure_uvicorn_logging() -> None:
        called["uvicorn_configure"] = True

    def _fake_get_uvicorn_server_config() -> UvicornServerConfig:
        return UvicornServerConfig(
            host="127.0.0.1",
            port=8000,
            workers=1,
            reload=False,
            timeout_keep_alive=5,
        )

    def _fake_uvicorn_run(*_args, **_kwargs) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr("datagovma_mcp.main.configure_logging", _fake_configure_logging)
    monkeypatch.setattr(
        "datagovma_mcp.main.configure_uvicorn_logging",
        _fake_configure_uvicorn_logging,
    )
    monkeypatch.setattr(
        "datagovma_mcp.main.get_uvicorn_server_config",
        _fake_get_uvicorn_server_config,
    )
    monkeypatch.setattr("datagovma_mcp.main.uvicorn.run", _fake_uvicorn_run)

    main.main()

    assert called["configure"] is True
    assert called["uvicorn_configure"] is True
