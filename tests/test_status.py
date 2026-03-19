import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.status import CKANAPIError, get_portal_status, register_status_tool
from tests.helpers import FakeMCP, mock_async_client_response


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
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/status_show",
        payload=json.dumps(payload),
    )

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
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/status_show",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(get_portal_status())


def test_get_portal_status_raises_on_non_json_response(monkeypatch: pytest.MonkeyPatch):
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/status_show",
        payload="<html>Request Rejected</html>",
    )

    with pytest.raises(CKANAPIError, match="non-JSON"):
        asyncio.run(get_portal_status())


def test_get_portal_status_raises_on_http_error(monkeypatch: pytest.MonkeyPatch):
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/status_show",
        payload='{"success": true}',
        status_code=502,
    )

    with pytest.raises(CKANAPIError, match="Request failed"):
        asyncio.run(get_portal_status())


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
    fake_mcp = FakeMCP()
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
