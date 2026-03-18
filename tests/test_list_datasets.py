import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.list_datasets import (
    CKANAPIError,
    list_datasets,
    register_list_datasets_tool,
)
from tests.helpers import FakeMCP, mock_async_client_response


def test_list_datasets_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": ["dataset-001", "dataset-002", "dataset-003"],
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.tools.list_datasets.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_list",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(list_datasets(limit=3, offset=6))

    assert result["list_url"].endswith("/package_list")
    assert result["limit"] == 3
    assert result["offset"] == 6
    assert result["returned"] == 3
    assert result["datasets"] == ["dataset-001", "dataset-002", "dataset-003"]

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["limit"] == 3
    assert call_params["offset"] == 6


def test_list_datasets_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.tools.list_datasets.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_list",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(list_datasets())


def test_list_datasets_validates_pagination_inputs():
    with pytest.raises(ValueError, match="`limit` must be >= 0"):
        asyncio.run(list_datasets(limit=-1))

    with pytest.raises(ValueError, match="`offset` must be >= 0"):
        asyncio.run(list_datasets(offset=-1))


def test_register_list_datasets_tool_registers_decorated_tool(monkeypatch: pytest.MonkeyPatch):
    async def _fake_list_datasets(
        limit: int,
        offset: int,
        *,
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "list_url": f"{api_base_url}/package_list",
            "limit": limit,
            "offset": offset,
            "returned": 2,
            "datasets": ["dataset-001", "dataset-002"],
        }

    monkeypatch.setattr("datagovma_mcp.tools.list_datasets.list_datasets", _fake_list_datasets)
    fake_mcp = FakeMCP()
    register_list_datasets_tool(cast(Any, fake_mcp))

    assert "list_datasets" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["list_datasets"](
            limit=2,
            offset=4,
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["limit"] == 2
    assert result["offset"] == 4
    assert result["datasets"] == ["dataset-001", "dataset-002"]
