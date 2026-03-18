"""Portal status tool for Morocco Open Data Government (data.gov.ma)."""

from __future__ import annotations

import logging
from typing import TypedDict

import httpx
from mcp.server.fastmcp import FastMCP

from datagovma_mcp.utils.ckan import (
    DEFAULT_API_BASE_URL,
    CKANAPIError,
    fetch_ckan_result,
)
from datagovma_mcp.utils.normalizers import as_optional_str, as_string_list

__all__ = ["CKANAPIError", "get_portal_status", "register_status_tool"]
logger = logging.getLogger(__name__)


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
    logger.info("Fetching portal status from %s", api_base_url)

    status_url, result = await fetch_ckan_result(
        api_base_url=api_base_url,
        action_name="status_show",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        client_factory=httpx.AsyncClient,
    )
    extensions = as_string_list(result.get("extensions"))
    logger.info(
        "Portal status fetched from %s with ckan_version=%s extensions=%s",
        status_url,
        as_optional_str(result.get("ckan_version")),
        len(extensions),
    )

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
    """Register the ``get_portal_status`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool get_portal_status")

    @mcp.tool(name="get_portal_status")
    async def get_portal_status_tool(
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> PortalStatus:
        """
        Check the Morocco Open Data Government portal runtime metadata.

        This tool calls CKAN ``status_show`` on ``data.gov.ma`` (or another
        compatible CKAN endpoint) and returns normalized portal information.
        Use it as a lightweight health/identity check before dataset queries.

        Args:
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``PortalStatus`` with site identity fields (title, URL, locale),
            CKAN version, and enabled extensions.
        """

        return await get_portal_status(
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
