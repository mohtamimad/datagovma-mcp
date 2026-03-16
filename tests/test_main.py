from datagovma_mcp import main


def test_main_runs_streamable_http(monkeypatch):
    called = {"inject": False, "transport": None, "create": False}

    def _fake_inject() -> None:
        called["inject"] = True

    class _FakeServer:
        def run(self, *, transport: str) -> None:
            called["transport"] = transport

    monkeypatch.setattr("datagovma_mcp.main.truststore.inject_into_ssl", _fake_inject)

    def _fake_create_server():
        called["create"] = True
        return _FakeServer()

    monkeypatch.setattr("datagovma_mcp.main.create_server", _fake_create_server)

    main.main()

    assert called["inject"] is True
    assert called["create"] is True
    assert called["transport"] == "streamable-http"


def test_main_handles_keyboard_interrupt(monkeypatch):
    called = {"inject": False, "create": False}

    def _fake_inject() -> None:
        called["inject"] = True

    class _FakeServer:
        def run(self, *, transport: str) -> None:
            _ = transport
            raise KeyboardInterrupt()

    monkeypatch.setattr("datagovma_mcp.main.truststore.inject_into_ssl", _fake_inject)

    def _fake_create_server():
        called["create"] = True
        return _FakeServer()

    monkeypatch.setattr("datagovma_mcp.main.create_server", _fake_create_server)

    main.main()

    assert called["inject"] is True
    assert called["create"] is True
