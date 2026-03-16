import asyncio
import json
from typing import Any, cast

import httpx
import pytest

from datagovma_mcp.tools.status import CKANAPIError, get_portal_status, register_status_tool


class _FakeResponse:
    def __init__(self, payload: str, status_code: int = 200):
        self.text = payload
        self.status_code = status_code
        self.request = httpx.Request("GET", "https://data.gov.ma/data/api/3/action/status_show")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}",
                request=self.request,
                response=httpx.Response(self.status_code, request=self.request),
            )

    def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeAsyncClient:
    def __init__(
        self,
        response: _FakeResponse | None = None,
        error: Exception | None = None,
        **_kwargs,
    ):
        self._response = response
        self._error = error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, _url: str) -> _FakeResponse:
        if self._error is not None:
            raise self._error
        if self._response is None:
            raise AssertionError("Fake client was called without a configured response")
        return self._response


def _mock_async_client_response(
    monkeypatch: pytest.MonkeyPatch,
    *,
    payload: str | None = None,
    status_code: int = 200,
    error: Exception | None = None,
) -> None:
    def _fake_async_client(*_args, **_kwargs):
        response = _FakeResponse(payload, status_code) if payload is not None else None
        return _FakeAsyncClient(response=response, error=error)

    monkeypatch.setattr("datagovma_mcp.tools.status.httpx.AsyncClient", _fake_async_client)


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
    _mock_async_client_response(monkeypatch, payload=json.dumps(payload))

    result = asyncio.run(get_portal_status())

    assert result["site_url"] == "https://data.gov.ma"
    assert result["ckan_version"] == "2.9.11"
    assert result["extensions"] == ["datastore", "validation"]
    assert result["status_url"].endswith("/status_show")


def test_get_portal_status_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    _mock_async_client_response(monkeypatch, payload=json.dumps(payload))

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(get_portal_status())


def test_get_portal_status_raises_on_non_json_response(monkeypatch: pytest.MonkeyPatch):
    _mock_async_client_response(monkeypatch, payload="<html>Request Rejected</html>")

    with pytest.raises(CKANAPIError, match="non-JSON"):
        asyncio.run(get_portal_status())


def test_get_portal_status_raises_on_http_error(monkeypatch: pytest.MonkeyPatch):
    _mock_async_client_response(monkeypatch, payload='{"success": true}', status_code=502)

    with pytest.raises(CKANAPIError, match="Request failed"):
        asyncio.run(get_portal_status())


class _FakeMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, name: str | None = None):
        def _decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func

        return _decorator


def test_register_status_tool_registers_decorated_tool(monkeypatch: pytest.MonkeyPatch):
    async def _fake_get_portal_status(
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "status_url": f"{api_base_url}/status_show",
            "site_title": "Test Portal",
            "site_description": "",
            "site_url": "https://data.gov.ma",
            "ckan_version": "2.9.11",
            "locale_default": "fr",
            "extensions": [],
        }

    monkeypatch.setattr("datagovma_mcp.tools.status.get_portal_status", _fake_get_portal_status)
    fake_mcp = _FakeMCP()
    register_status_tool(cast(Any, fake_mcp))

    assert "get_portal_status" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["get_portal_status"](
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["site_title"] == "Test Portal"
    assert result["status_url"] == "https://example.invalid/api/3/action/status_show"
