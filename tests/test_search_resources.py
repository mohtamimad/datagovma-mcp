import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.search_resources import (
    CKANAPIError,
    register_search_resources_tool,
    search_resources,
)
from tests.helpers import FakeMCP, mock_async_client_response


def test_search_resources_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "count": 2,
            "sort": "last_modified desc",
            "results": [
                {
                    "id": "resource-1",
                    "name": "budget-2025-csv",
                    "format": "CSV",
                },
                {
                    "id": "resource-2",
                    "name": "budget-2026-csv",
                    "format": "CSV",
                },
            ],
        },
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/resource_search",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(
        search_resources(
            query=" name:budget ",
            limit=5,
            offset=10,
            sort="last_modified desc",
        )
    )

    assert result["search_url"].endswith("/resource_search")
    assert result["query"] == "name:budget"
    assert result["field"] == "name"
    assert result["value"] == "budget"
    assert result["limit"] == 5
    assert result["offset"] == 10
    assert result["sort"] == "last_modified desc"
    assert result["sort_applied"] == "last_modified desc"
    assert result["total_count"] == 2
    assert result["resource_count"] == 2
    assert result["resources"][0]["id"] == "resource-1"

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["query"] == "name:budget"
    assert call_params["limit"] == 5
    assert call_params["offset"] == 10
    assert call_params["order_by"] == "last_modified desc"


def test_search_resources_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/resource_search",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(search_resources(query="name:budget"))


def test_search_resources_validates_inputs():
    with pytest.raises(ValueError, match="cannot be empty"):
        asyncio.run(search_resources(query="   "))

    with pytest.raises(ValueError, match="field:value format"):
        asyncio.run(search_resources(query="budget"))

    with pytest.raises(ValueError, match="`limit` must be >= 0"):
        asyncio.run(search_resources(query="name:budget", limit=-1))

    with pytest.raises(ValueError, match="`offset` must be >= 0"):
        asyncio.run(search_resources(query="name:budget", offset=-1))


def test_search_resources_handles_waf_html_response(monkeypatch: pytest.MonkeyPatch):
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/resource_search",
        payload="<html><title>Request Rejected</title><body>Request Rejected</body></html>",
    )

    with pytest.raises(CKANAPIError, match="blocked by upstream WAF"):
        asyncio.run(search_resources(query="name:budget"))


def test_register_search_resources_tool_registers_decorated_tool(
    monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_search_resources(
        query: str,
        limit: int,
        offset: int,
        sort: str | None,
        *,
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "search_url": f"{api_base_url}/resource_search",
            "query": query,
            "field": "name",
            "value": "budget",
            "limit": limit,
            "offset": offset,
            "sort": sort,
            "sort_applied": sort,
            "total_count": 1,
            "resource_count": 1,
            "resources": [{"id": "resource-1"}],
        }

    monkeypatch.setattr(
        "datagovma_mcp.tools.search_resources.search_resources",
        _fake_search_resources,
    )
    fake_mcp = FakeMCP()
    register_search_resources_tool(cast(Any, fake_mcp))

    assert "search_resources" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["search_resources"](
            query="name:budget",
            limit=2,
            offset=1,
            sort="last_modified desc",
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["query"] == "name:budget"
    assert result["limit"] == 2
    assert result["resource_count"] == 1
