"""Status tool implementation for the data.gov.ma CKAN API."""

from __future__ import annotations

from typing import TypedDict

import httpx
from mcp.server.fastmcp import FastMCP

from datagovma_mcp.utils.ckan import (
    DEFAULT_API_BASE_URL,
    CKANAPIError,
    as_optional_str,
    as_string_list,
    fetch_ckan_result,
)

__all__ = ["CKANAPIError", "get_portal_status", "register_status_tool"]


class PortalStatus(TypedDict):
    """Normalized payload shape returned by ``get_portal_status``."""

    api_base_url: str
    status_url: str
    site_title: str | None
    site_description: str | None
    site_url: str | None
    ckan_version: str | None
    locale_default: str | None
    extensions: list[str]


async def get_portal_status(
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> PortalStatus:
    """
    Fetch and normalize portal metadata from CKAN ``status_show``.

    Args:
        api_base_url: CKAN Action API base URL (for example,
            ``https://data.gov.ma/data/api/3/action``).
        timeout_seconds: Upstream request timeout in seconds.
        verify_ssl: Whether to validate HTTPS certificates for the upstream call.

    Returns:
        A normalized payload with stable keys:
        - ``api_base_url``: Base CKAN Action API URL used for the request.
        - ``status_url``: Resolved ``status_show`` endpoint URL called.
        - ``site_title``: Portal title from CKAN settings, if present.
        - ``site_description``: Portal description from CKAN settings, if present.
        - ``site_url``: Public portal root URL, if present.
        - ``ckan_version``: CKAN server version string, if present.
        - ``locale_default``: Default locale code, if present.
        - ``extensions``: Enabled CKAN extension names (empty list when absent).

    Raises:
        CKANAPIError: If the request fails, times out, returns non-JSON data,
            returns ``success: false``, or has an invalid CKAN envelope.
    """

    status_url, result = await fetch_ckan_result(
        api_base_url=api_base_url,
        action_name="status_show",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        client_factory=httpx.AsyncClient,
    )
    extensions = as_string_list(result.get("extensions"))

    return {
        "api_base_url": api_base_url,
        "status_url": status_url,
        "site_title": as_optional_str(result.get("site_title")),
        "site_description": as_optional_str(result.get("site_description")),
        "site_url": as_optional_str(result.get("site_url")),
        "ckan_version": as_optional_str(result.get("ckan_version")),
        "locale_default": as_optional_str(result.get("locale_default")),
        "extensions": extensions,
    }


def register_status_tool(mcp: FastMCP) -> None:
    """Register the ``get_portal_status`` MCP tool on a FastMCP instance."""

    @mcp.tool(name="get_portal_status")
    async def get_portal_status_tool(
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> PortalStatus:
        """
        Return normalized metadata from the CKAN ``status_show`` endpoint.

        Args:
            api_base_url: CKAN Action API base URL.
            timeout_seconds: Upstream request timeout in seconds.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            A ``PortalStatus`` object with portal identity and runtime metadata.
        """

        return await get_portal_status(
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
