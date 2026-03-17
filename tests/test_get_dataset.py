import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.get_dataset import CKANAPIError, get_dataset, register_get_dataset_tool
from tests.helpers import FakeMCP, mock_async_client_response


def test_get_dataset_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "id": "9f1f9f62-0e49-4b50-9257-8c2a7e92770e",
            "name": "budget-2025",
            "title": "Budget 2025",
            "notes": "Annual budget dataset",
            "state": "active",
            "private": False,
            "metadata_created": "2025-01-01T00:00:00.000000",
            "metadata_modified": "2025-02-01T00:00:00.000000",
            "organization": {"name": "ministry-of-finance", "title": "Ministry of Finance"},
            "tags": [{"name": "budget"}, {"name": "finance"}],
            "groups": [{"name": "statistics"}],
            "resources": [
                {"id": "resource-1", "name": "Budget CSV", "format": "CSV"},
                {"id": "resource-2", "name": "Budget XLSX", "format": "XLSX"},
            ],
        },
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.tools.get_dataset.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_show",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(get_dataset("  budget-2025  "))

    assert result["requested_id"] == "budget-2025"
    assert result["id"] == "9f1f9f62-0e49-4b50-9257-8c2a7e92770e"
    assert result["title"] == "Budget 2025"
    assert result["organization_name"] == "ministry-of-finance"
    assert result["organization_title"] == "Ministry of Finance"
    assert result["tags"] == ["budget", "finance"]
    assert result["groups"] == ["statistics"]
    assert result["resource_count"] == 2
    assert result["resources"][0]["id"] == "resource-1"
    assert result["dataset_url"].endswith("/package_show")

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["id"] == "budget-2025"


def test_get_dataset_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.tools.get_dataset.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/package_show",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(get_dataset("budget-2025"))


def test_get_dataset_validates_id():
    with pytest.raises(ValueError, match="cannot be empty"):
        asyncio.run(get_dataset("   "))


def test_register_get_dataset_tool_registers_decorated_tool(monkeypatch: pytest.MonkeyPatch):
    async def _fake_get_dataset(
        id: str,
        *,
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "dataset_url": f"{api_base_url}/package_show",
            "requested_id": id,
            "id": "dataset-uuid",
            "name": id,
            "title": "Dataset title",
            "notes": None,
            "state": "active",
            "private": False,
            "metadata_created": None,
            "metadata_modified": None,
            "organization_name": "ministry-of-finance",
            "organization_title": "Ministry of Finance",
            "tags": ["budget"],
            "groups": ["statistics"],
            "resource_count": 1,
            "resources": [{"id": "resource-1"}],
        }

    monkeypatch.setattr("datagovma_mcp.tools.get_dataset.get_dataset", _fake_get_dataset)
    fake_mcp = FakeMCP()
    register_get_dataset_tool(cast(Any, fake_mcp))

    assert "get_dataset" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["get_dataset"](
            id="budget-2025",
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["requested_id"] == "budget-2025"
    assert result["id"] == "dataset-uuid"
    assert result["resources"][0]["id"] == "resource-1"
