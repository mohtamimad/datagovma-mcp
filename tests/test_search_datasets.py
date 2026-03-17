import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.search_datasets import (
    CKANAPIError,
    register_search_datasets_tool,
    search_datasets,
)
from tests.helpers import FakeMCP, mock_async_client_response


def test_search_datasets_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "count": 2,
            "sort": "metadata_modified desc",
            "facets": {"organization": {"ministry-of-finance": 2}},
            "search_facets": {"organization": {"items": [{"name": "ministry-of-finance"}]}},
            "results": [
                {"id": "dataset-1", "title": "Budget 2025"},
                {"id": "dataset-2", "title": "Budget 2026"},
            ],
        },
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.tools.search_datasets.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_search",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(
        search_datasets(
            q="budget",
            fq="organization:ministry-of-finance",
            rows=5,
            start=10,
            sort="metadata_modified desc",
            facet_fields=["organization", "tags", "organization"],
        )
    )

    assert result["count"] == 2
    assert result["returned"] == 2
    assert result["rows"] == 5
    assert result["start"] == 10
    assert result["query"] == "budget"
    assert result["filter_query"] == "organization:ministry-of-finance"
    assert result["sort"] == "metadata_modified desc"
    assert result["sort_applied"] == "metadata_modified desc"
    assert result["search_url"].endswith("/package_search")
    assert result["facets"]["organization"]["ministry-of-finance"] == 2
    assert result["results"][0]["id"] == "dataset-1"

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["q"] == "budget"
    assert call_params["fq"] == "organization:ministry-of-finance"
    assert call_params["rows"] == 5
    assert call_params["start"] == 10
    assert call_params["sort"] == "metadata_modified desc"
    assert call_params["facet"] == "true"
    facet_field = cast(str, call_params["facet.field"])
    assert json.loads(facet_field) == ["organization", "tags"]


def test_search_datasets_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.tools.search_datasets.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_search",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(search_datasets(q="economy"))


def test_register_search_datasets_tool_registers_decorated_tool(
    monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_search_datasets(
        q: str | None,
        fq: str | None,
        rows: int,
        start: int,
        sort: str | None,
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
            "rows": rows,
            "start": start,
            "sort": sort,
            "sort_applied": sort,
            "count": 1,
            "returned": 1,
            "results": [{"id": "dataset-1"}],
            "facets": {"organization": {"ministry-of-finance": 1}},
            "search_facets": {},
        }

    monkeypatch.setattr(
        "datagovma_mcp.tools.search_datasets.search_datasets",
        _fake_search_datasets,
    )
    fake_mcp = FakeMCP()
    register_search_datasets_tool(cast(Any, fake_mcp))

    assert "search_datasets" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["search_datasets"](
            q="budget",
            fq="organization:ministry-of-finance",
            rows=5,
            start=0,
            sort="metadata_modified desc",
            facet_fields=["organization"],
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["query"] == "budget"
    assert result["rows"] == 5
    assert result["results"][0]["id"] == "dataset-1"
