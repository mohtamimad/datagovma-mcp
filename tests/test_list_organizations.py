import asyncio
import json
from typing import Any, cast

import pytest

from datagovma_mcp.tools.list_organizations import (
    CKANAPIError,
    list_organizations,
    register_list_organizations_tool,
)
from tests.helpers import FakeMCP, mock_async_client_response


def test_list_organizations_success(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": True,
        "result": ["ministry-of-finance", "high-commission-for-planning"],
    }
    calls: list[dict[str, object]] = []
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/organization_list",
        payload=json.dumps(payload),
        calls=calls,
    )

    result = asyncio.run(list_organizations(limit=2, offset=4))

    assert result["list_url"].endswith("/organization_list")
    assert result["limit"] == 2
    assert result["offset"] == 4
    assert result["organization_count"] == 2
    assert result["organizations"] == [
        "ministry-of-finance",
        "high-commission-for-planning",
    ]

    assert len(calls) == 1
    call_params = cast(dict[str, object], calls[0]["params"])
    assert call_params["all_fields"] == "false"
    assert call_params["limit"] == 2
    assert call_params["offset"] == 4


def test_list_organizations_raises_when_success_false(monkeypatch: pytest.MonkeyPatch):
    payload = {
        "success": False,
        "error": {"message": "Not authorized"},
    }
    mock_async_client_response(
        monkeypatch,
        target="datagovma_mcp.utils.ckan.httpx.AsyncClient",
        request_url="https://data.gov.ma/data/api/3/action/organization_list",
        payload=json.dumps(payload),
    )

    with pytest.raises(CKANAPIError, match="Not authorized"):
        asyncio.run(list_organizations())


def test_list_organizations_validates_pagination_inputs():
    with pytest.raises(ValueError, match="`limit` must be >= 0"):
        asyncio.run(list_organizations(limit=-1))

    with pytest.raises(ValueError, match="`offset` must be >= 0"):
        asyncio.run(list_organizations(offset=-1))


def test_register_list_organizations_tool_registers_decorated_tool(
    monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_list_organizations(
        limit: int,
        offset: int,
        *,
        api_base_url: str,
        timeout_seconds: float,
        verify_ssl: bool,
    ):
        return {
            "api_base_url": api_base_url,
            "list_url": f"{api_base_url}/organization_list",
            "limit": limit,
            "offset": offset,
            "organization_count": 2,
            "organizations": ["ministry-of-finance", "high-commission-for-planning"],
        }

    monkeypatch.setattr(
        "datagovma_mcp.tools.list_organizations.list_organizations",
        _fake_list_organizations,
    )
    fake_mcp = FakeMCP()
    register_list_organizations_tool(cast(Any, fake_mcp))

    assert "list_organizations" in fake_mcp.tools

    result = asyncio.run(
        fake_mcp.tools["list_organizations"](
            limit=2,
            offset=1,
            api_base_url="https://example.invalid/api/3/action",
            timeout_seconds=1.0,
            verify_ssl=False,
        )
    )

    assert result["limit"] == 2
    assert result["offset"] == 1
    assert result["organizations"] == [
        "ministry-of-finance",
        "high-commission-for-planning",
    ]
