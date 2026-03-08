import json

import pytest

from tools.status import CKANAPIError, get_portal_status


class _FakeResponse:
    def __init__(self, payload: str):
        self._payload = payload.encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _mock_urlopen_response(monkeypatch: pytest.MonkeyPatch, payload: str) -> None:
    def _fake_urlopen(*_args, **_kwargs):
        return _FakeResponse(payload)

    monkeypatch.setattr("tools.status.urlopen", _fake_urlopen)


def test_get_portal_status_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "site_title": "Portail Open Data",
            "site_description": "",
            "site_url": "https://data.gov.ma",
            "ckan_version": "2.9.11",
            "locale_default": "fr",
            "extensions": ["datastore", "validation"],
        },
    }
    _mock_urlopen_response(monkeypatch, json.dumps(payload))

    result = get_portal_status()

    assert result["site_url"] == "https://data.gov.ma"
    assert result["ckan_version"] == "2.9.11"
    assert result["extensions"] == ["datastore", "validation"]
    assert result["status_url"].endswith("/status_show")


def test_get_portal_status_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    _mock_urlopen_response(monkeypatch, json.dumps(payload))

    with pytest.raises(CKANAPIError, match="Not authorized"):
        get_portal_status()


def test_get_portal_status_raises_on_non_json_response(monkeypatch: pytest.MonkeyPatch):
    _mock_urlopen_response(monkeypatch, "<html>Request Rejected</html>")

    with pytest.raises(CKANAPIError, match="non-JSON"):
        get_portal_status()
