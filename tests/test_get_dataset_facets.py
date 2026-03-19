import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.get_dataset_facets import (
    CKANAPIError,
    get_dataset_facets,
    register_get_dataset_facets_tool,
)
from tests.helpers import FakeMCP, mock_async_client_response


def test_get_dataset_facets_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "count": 663,
            "sort": None,
            "facets": {
                "organization": {"ministry-of-finance": 42},
                "groups": {"economy": 30},
                "tags": {"budget": 15},
            },
            "search_facets": {"organization": {"items": [{"name": "ministry-of-finance"}]}},
            "results": [],
        },
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_search",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(
        get_dataset_facets(
            q="budget",
            fq="organization:ministry-of-finance",
            facet_fields=["organization", "tags", "groups", "organization"],
        )
    )

    assert result["search_url"].endswith("/package_search")
    assert result["query"] == "budget"
    assert result["filter_query"] == "organization:ministry-of-finance"
    assert result["facet_fields"] == ["organization", "tags", "groups"]
    assert result["facet_field_count"] == 3
    assert result["total_count"] == 663
    assert result["facets"]["organization"]["ministry-of-finance"] == 42

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["q"] == "budget"
    assert call_params["fq"] == "organization:ministry-of-finance"
    assert call_params["rows"] == 0
    assert call_params["start"] == 0
    assert call_params["facet"] == "true"
    facet_field = cast(str, call_params["facet.field"])
    assert json.loads(facet_field) == ["organization", "tags", "groups"]


def test_get_dataset_facets_uses_default_facet_fields(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "count": 1,
            "sort": None,
            "facets": {
                "tags": {"budget": 1},
                "groups": {"economy": 1},
                "organization": {"ministry-of-finance": 1},
            },
            "search_facets": {},
            "results": [],
        },
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_search",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(get_dataset_facets())

    assert result["facet_fields"] == ["tags", "groups", "organization"]
    assert result["facet_field_count"] == 3

    call_params = cast(dict[str, object], calls[0]["params"])
    facet_field = cast(str, call_params["facet.field"])
    assert json.loads(facet_field) == ["tags", "groups", "organization"]


def test_get_dataset_facets_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_search",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(get_dataset_facets())


def test_get_dataset_facets_validates_facet_fields():
    with pytest.raises(ValueError, match="`facet_fields` must contain only strings"):
        asyncio.run(get_dataset_facets(facet_fields=["organization", cast(Any, 42)]))

    with pytest.raises(ValueError, match="`facet_fields` cannot contain empty values"):
        asyncio.run(get_dataset_facets(facet_fields=["organization", "   "]))


def test_register_get_dataset_facets_tool_registers_decorated_tool(
    monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_get_dataset_facets(
        q: str | None,
        fq: str | None,
        facet_fields: list[str] | None,
        *,
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "search_url": f"{api_base_url}/package_search",
            "query": q,
            "filter_query": fq,
            "facet_fields": facet_fields or ["tags", "groups", "organization"],
            "facet_field_count": 3,
            "total_count": 10,
            "facets": {"organization": {"ministry-of-finance": 10}},
            "search_facets": {},
        }

    monkeypatch.setattr(
        "datagovma_mcp.tools.get_dataset_facets.get_dataset_facets",
        _fake_get_dataset_facets,
    )
    fake_mcp = FakeMCP()
    register_get_dataset_facets_tool(cast(Any, fake_mcp))

    assert "get_dataset_facets" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["get_dataset_facets"](
            q="budget",
            fq="organization:ministry-of-finance",
            facet_fields=["organization", "tags"],
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["query"] == "budget"
    assert result["facet_fields"] == ["organization", "tags"]
    assert result["total_count"] == 10
