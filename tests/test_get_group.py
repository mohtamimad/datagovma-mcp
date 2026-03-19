import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.get_group import CKANAPIError, get_group, register_get_group_tool
from tests.helpers import FakeMCP, mock_async_client_response


def test_get_group_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "id": "group-uuid",
            "name": "economy",
            "title": "Economy",
            "description": "Economic indicators and statistics",
            "state": "active",
            "type": "group",
            "created": "2025-01-01T00:00:00.000000",
            "image_url": "https://data.gov.ma/uploads/group/economy.png",
            "package_count": 12,
            "packages": [
                {"id": "dataset-1", "name": "gdp-2025", "title": "GDP 2025"},
                {"id": "dataset-2", "name": "inflation-2025", "title": "Inflation 2025"},
            ],
        },
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/group_show",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(get_group("  economy  ", include_datasets=True))

    assert result["requested_id"] == "economy"
    assert result["include_datasets"] is True
    assert result["id"] == "group-uuid"
    assert result["title"] == "Economy"
    assert result["package_count"] == 12
    assert result["dataset_count"] == 2
    assert result["datasets"][0]["name"] == "gdp-2025"
    assert result["group_show_url"].endswith("/group_show")

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["id"] == "economy"
    assert call_params["include_datasets"] == "true"


def test_get_group_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/group_show",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(get_group("economy"))


def test_get_group_validates_inputs():
    with pytest.raises(ValueError, match="cannot be empty"):
        asyncio.run(get_group("   "))

    with pytest.raises(ValueError, match="`include_datasets` must be a boolean"):
        asyncio.run(get_group("economy", include_datasets=cast(Any, "yes")))


def test_register_get_group_tool_registers_decorated_tool(
    monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_get_group(
        id: str,
        include_datasets: bool,
        *,
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "group_show_url": f"{api_base_url}/group_show",
            "requested_id": id,
            "include_datasets": include_datasets,
            "id": "group-uuid",
            "name": id,
            "title": "Economy",
            "description": None,
            "state": "active",
            "group_type": "group",
            "created": None,
            "image_url": None,
            "package_count": 1,
            "dataset_count": 1,
            "datasets": [{"id": "dataset-1", "name": "gdp-2025"}],
        }

    monkeypatch.setattr(
        "datagovma_mcp.tools.get_group.get_group",
        _fake_get_group,
    )
    fake_mcp = FakeMCP()
    register_get_group_tool(cast(Any, fake_mcp))

    assert "get_group" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["get_group"](
            id="economy",
            include_datasets=True,
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["requested_id"] == "economy"
    assert result["include_datasets"] is True
    assert result["datasets"][0]["name"] == "gdp-2025"
