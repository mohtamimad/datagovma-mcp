import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.get_organization import (
    CKANAPIError,
    get_organization,
    register_get_organization_tool,
)
from tests.helpers import FakeMCP, mock_async_client_response


def test_get_organization_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": {
            "id": "organization-uuid",
            "name": "ministry-of-finance",
            "title": "Ministry of Finance",
            "description": "Public finance authority",
            "state": "active",
            "type": "organization",
            "created": "2025-01-01T00:00:00.000000",
            "image_url": "https://data.gov.ma/uploads/group/ministry.png",
            "package_count": 42,
            "packages": [
                {"id": "dataset-1", "name": "budget-2025", "title": "Budget 2025"},
                {"id": "dataset-2", "name": "spending-2024", "title": "Spending 2024"},
            ],
        },
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/organization_show",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(get_organization("  ministry-of-finance  ", include_datasets=True))

    assert result["requested_id"] == "ministry-of-finance"
    assert result["include_datasets"] is True
    assert result["id"] == "organization-uuid"
    assert result["title"] == "Ministry of Finance"
    assert result["package_count"] == 42
    assert result["datasets_returned"] == 2
    assert result["datasets"][0]["name"] == "budget-2025"
    assert result["organization_show_url"].endswith("/organization_show")

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["id"] == "ministry-of-finance"
    assert call_params["include_datasets"] == "true"


def test_get_organization_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/organization_show",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(get_organization("ministry-of-finance"))


def test_get_organization_validates_inputs():
    with pytest.raises(ValueError, match="cannot be empty"):
        asyncio.run(get_organization("   "))

    with pytest.raises(ValueError, match="`include_datasets` must be a boolean"):
        asyncio.run(get_organization("ministry-of-finance", include_datasets=cast(Any, "yes")))


def test_register_get_organization_tool_registers_decorated_tool(
    monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_get_organization(
        id: str,
        include_datasets: bool,
        *,
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "organization_show_url": f"{api_base_url}/organization_show",
            "requested_id": id,
            "include_datasets": include_datasets,
            "id": "organization-uuid",
            "name": id,
            "title": "Ministry of Finance",
            "description": None,
            "state": "active",
            "organization_type": "organization",
            "created": None,
            "image_url": None,
            "package_count": 1,
            "datasets_returned": 1,
            "datasets": [{"id": "dataset-1", "name": "budget-2025"}],
        }

    monkeypatch.setattr(
        "datagovma_mcp.tools.get_organization.get_organization",
        _fake_get_organization,
    )
    fake_mcp = FakeMCP()
    register_get_organization_tool(cast(Any, fake_mcp))

    assert "get_organization" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["get_organization"](
            id="ministry-of-finance",
            include_datasets=True,
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["requested_id"] == "ministry-of-finance"
    assert result["include_datasets"] is True
    assert result["datasets"][0]["name"] == "budget-2025"
