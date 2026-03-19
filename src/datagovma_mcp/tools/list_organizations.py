"""Organization listing tool for Morocco Open Data Government (data.gov.ma)."""

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

__all__ = ["CKANAPIError", "list_organizations", "register_list_organizations_tool"]
logger = logging.getLogger(__name__)


class OrganizationListResult(TypedDict):
    """Normalized payload shape returned by ``list_organizations``."""

    api_base_url: str
    list_url: str
    limit: int
    offset: int
    organization_count: int
    organizations: list[str]


async def list_organizations(
    limit: int = 100,
    offset: int = 0,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> OrganizationListResult:
    """
    List organization names from CKAN ``organization_list`` with pagination support.

    Args:
        limit: Number of organization names requested (example: ``100``).
        offset: Zero-based pagination offset (example: ``0`` for first page).
        api_base_url: CKAN Action API base URL
            (example: ``"https://data.gov.ma/data/api/3/action"``).
        timeout_seconds: Upstream request timeout in seconds (example: ``15.0``).
        verify_ssl: Whether to validate HTTPS certificates for the upstream call
            (example: ``True``).

    Returns:
        A normalized payload with requested pagination values and organization
        names.

    Raises:
        ValueError: If input parameters fail validation.
        CKANAPIError: If the request fails, times out, returns non-JSON data,
            returns ``success: false``, or has an invalid CKAN envelope.
    """

    normalized_limit = validate_non_negative_int(limit, field_name="limit")
    normalized_offset = validate_non_negative_int(offset, field_name="offset")
    logger.info(
        "Listing organizations from %s limit=%s offset=%s",
        api_base_url,
        normalized_limit,
        normalized_offset,
    )

    list_url, raw_result = await fetch_ckan_action_result(
        api_base_url=api_base_url,
        action_name="organization_list",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        query_params={
            "all_fields": "false",
            "limit": normalized_limit,
            "offset": normalized_offset,
        },
    )
    organizations = as_required_str_list(raw_result, field_name="result")
    logger.info(
        "Organization list fetched from %s organization_count=%s",
        list_url,
        len(organizations),
    )

    return {
        "api_base_url": api_base_url,
        "list_url": list_url,
        "limit": normalized_limit,
        "offset": normalized_offset,
        "organization_count": len(organizations),
        "organizations": organizations,
    }


def register_list_organizations_tool(mcp: FastMCP) -> None:
    """Register the ``list_organizations`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool list_organizations")

    @mcp.tool(name="list_organizations")
    async def list_organizations_tool(
        limit: int = 100,
        offset: int = 0,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> OrganizationListResult:
        """
        List organizations from Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``organization_list`` and is optimized for
        lightweight organization discovery with explicit paging controls.

        Args:
            limit: Number of organization names requested (example: ``100``).
            offset: Zero-based pagination offset (example: ``0``).
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``OrganizationListResult`` with pagination metadata and organization
            names.
        """

        return await list_organizations(
            limit=limit,
            offset=offset,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
