import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.get_resource import (
    CKANAPIError,
    get_resource,
    register_get_resource_tool,
)
from tests.helpers import FakeMCP, mock_async_client_response


def test_get_resource_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "id": "7f5a0f8e-2a6c-4f79-8655-30101df169f9",
            "name": "budget-2025-csv",
            "description": "Budget 2025 in CSV format",
            "format": "CSV",
            "mimetype": "text/csv",
            "mimetype_inner": None,
            "url": "https://data.gov.ma/dataset/budget-2025/resource/budget-2025.csv",
            "state": "active",
            "resource_type": "file.upload",
            "created": "2025-01-01T00:00:00.000000",
            "last_modified": "2025-02-01T00:00:00.000000",
            "size": 2048,
            "position": 0,
            "package_id": "9f1f9f62-0e49-4b50-9257-8c2a7e92770e",
        },
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.tools.get_resource.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/resource_show",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(get_resource("  7f5a0f8e-2a6c-4f79-8655-30101df169f9  "))

    assert result["requested_id"] == "7f5a0f8e-2a6c-4f79-8655-30101df169f9"
    assert result["id"] == "7f5a0f8e-2a6c-4f79-8655-30101df169f9"
    assert result["format"] == "CSV"
    assert result["mimetype"] == "text/csv"
    assert (
        result["download_url"] == "https://data.gov.ma/dataset/budget-2025/resource/budget-2025.csv"
    )
    assert result["package_id"] == "9f1f9f62-0e49-4b50-9257-8c2a7e92770e"
    assert result["resource_show_url"].endswith("/resource_show")

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["id"] == "7f5a0f8e-2a6c-4f79-8655-30101df169f9"


def test_get_resource_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.tools.get_resource.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/resource_show",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(get_resource("7f5a0f8e-2a6c-4f79-8655-30101df169f9"))


def test_get_resource_validates_id():
    with pytest.raises(ValueError, match="cannot be empty"):
        asyncio.run(get_resource("   "))


def test_register_get_resource_tool_registers_decorated_tool(
    monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_get_resource(
        id: str,
        *,
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "resource_show_url": f"{api_base_url}/resource_show",
            "requested_id": id,
            "id": id,
            "name": "budget-2025-csv",
            "description": None,
            "format": "CSV",
            "mimetype": "text/csv",
            "mimetype_inner": None,
            "download_url": "https://example.invalid/budget.csv",
            "state": "active",
            "resource_type": "file.upload",
            "created": None,
            "last_modified": None,
            "size_bytes": 123,
            "position": 0,
            "package_id": "dataset-uuid",
        }

    monkeypatch.setattr("datagovma_mcp.tools.get_resource.get_resource", _fake_get_resource)
    fake_mcp = FakeMCP()
    register_get_resource_tool(cast(Any, fake_mcp))

    assert "get_resource" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["get_resource"](
            id="resource-uuid",
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["requested_id"] == "resource-uuid"
    assert result["format"] == "CSV"
    assert result["package_id"] == "dataset-uuid"
