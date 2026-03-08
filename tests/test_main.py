import main


def test_main_runs_streamable_http(monkeypatch):
    called = {"inject": False, "transport": None}

    def _fake_inject() -> None:
        called["inject"] = True

    def _fake_run(*, transport: str) -> None:
        called["transport"] = transport

    monkeypatch.setattr("main.truststore.inject_into_ssl", _fake_inject)
    monkeypatch.setattr("main.mcp.run", _fake_run)

    main.main()

    assert called["inject"] is True
    assert called["transport"] == "streamable-http"
