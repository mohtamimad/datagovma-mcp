"""Group listing tool for Morocco Open Data Government (data.gov.ma)."""

from __future__ import annotations

import logging
from typing import TypedDict

from mcp.server.fastmcp import FastMCP

from datagovma_mcp.utils.ckan import (
    DEFAULT_API_BASE_URL,
    CKANAPIError,
    as_required_str_list,
    fetch_ckan_action_result,
)
from datagovma_mcp.utils.validators import validate_non_negative_int

__all__ = ["CKANAPIError", "list_groups", "register_list_groups_tool"]
logger = logging.getLogger(__name__)


class GroupListResult(TypedDict):
    """Normalized payload shape returned by ``list_groups``."""

    api_base_url: str
    list_url: str
    limit: int
    offset: int
    group_count: int
    groups: list[str]


async def list_groups(
    limit: int = 100,
    offset: int = 0,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> GroupListResult:
    """
    List group names from CKAN ``group_list`` with pagination support.

    Args:
        limit: Number of group names requested (example: ``100``).
        offset: Zero-based pagination offset (example: ``0`` for first page).
        api_base_url: CKAN Action API base URL
            (example: ``"https://data.gov.ma/data/api/3/action"``).
        timeout_seconds: Upstream request timeout in seconds (example: ``15.0``).
        verify_ssl: Whether to validate HTTPS certificates for the upstream call
            (example: ``True``).

    Returns:
        A normalized payload with requested pagination values and group names.

    Raises:
        ValueError: If input parameters fail validation.
        CKANAPIError: If the request fails, times out, returns non-JSON data,
            returns ``success: false``, or has an invalid CKAN envelope.
    """

    normalized_limit = validate_non_negative_int(limit, field_name="limit")
    normalized_offset = validate_non_negative_int(offset, field_name="offset")
    logger.info(
        "Listing groups from %s limit=%s offset=%s",
        api_base_url,
        normalized_limit,
        normalized_offset,
    )

    list_url, raw_result = await fetch_ckan_action_result(
        api_base_url=api_base_url,
        action_name="group_list",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        query_params={
            "all_fields": "false",
            "limit": normalized_limit,
            "offset": normalized_offset,
        },
    )
    groups = as_required_str_list(raw_result, field_name="result")
    logger.info("Group list fetched from %s group_count=%s", list_url, len(groups))

    return {
        "api_base_url": api_base_url,
        "list_url": list_url,
        "limit": normalized_limit,
        "offset": normalized_offset,
        "group_count": len(groups),
        "groups": groups,
    }


def register_list_groups_tool(mcp: FastMCP) -> None:
    """Register the ``list_groups`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool list_groups")

    @mcp.tool(name="list_groups")
    async def list_groups_tool(
        limit: int = 100,
        offset: int = 0,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> GroupListResult:
        """
        List groups from Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``group_list`` and is optimized for lightweight
        group discovery with explicit paging controls.

        Args:
            limit: Number of group names requested (example: ``100``).
            offset: Zero-based pagination offset (example: ``0``).
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``GroupListResult`` with pagination metadata and group names.
        """

        return await list_groups(
            limit=limit,
            offset=offset,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
