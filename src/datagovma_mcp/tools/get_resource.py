"""Resource detail tool for Morocco Open Data Government (data.gov.ma)."""

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
from datagovma_mcp.utils.normalizers import as_optional_int, as_optional_str
from datagovma_mcp.utils.validators import validate_non_empty_str

__all__ = ["CKANAPIError", "get_resource", "register_get_resource_tool"]
logger = logging.getLogger(__name__)


class ResourceDetails(TypedDict):
    """Normalized payload shape returned by ``get_resource``."""

    api_base_url: str
    resource_show_url: str
    requested_id: str
    id: str | None
    name: str | None
    description: str | None
    format: str | None
    mimetype: str | None
    mimetype_inner: str | None
    download_url: str | None
    state: str | None
    resource_type: str | None
    created: str | None
    last_modified: str | None
    size_bytes: int | None
    position: int | None
    package_id: str | None


async def get_resource(
    id: str,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> ResourceDetails:
    """
    Fetch and normalize a single resource from CKAN ``resource_show``.

    Args:
        id: Resource identifier accepted by CKAN (UUID).
        api_base_url: CKAN Action API base URL.
        timeout_seconds: Upstream request timeout in seconds.
        verify_ssl: Whether to validate HTTPS certificates for the upstream call.

    Returns:
        A normalized payload with the requested resource metadata.

    Raises:
        ValueError: If ``id`` is not a non-empty string.
        CKANAPIError: If the request fails, times out, returns non-JSON data,
            returns ``success: false``, or has an invalid CKAN envelope.
    """

    normalized_id = validate_non_empty_str(id, field_name="id")
    logger.info("Fetching resource id=%s from %s", normalized_id, api_base_url)

    resource_show_url, result = await fetch_ckan_result(
        api_base_url=api_base_url,
        action_name="resource_show",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        query_params={"id": normalized_id},
        client_factory=httpx.AsyncClient,
    )
    logger.info(
        "Resource fetched from %s id=%s package_id=%s format=%s",
        resource_show_url,
        normalized_id,
        as_optional_str(result.get("package_id")),
        as_optional_str(result.get("format")),
    )

    return {
        "api_base_url": api_base_url,
        "resource_show_url": resource_show_url,
        "requested_id": normalized_id,
        "id": as_optional_str(result.get("id")),
        "name": as_optional_str(result.get("name")),
        "description": as_optional_str(result.get("description")),
        "format": as_optional_str(result.get("format")),
        "mimetype": as_optional_str(result.get("mimetype")),
        "mimetype_inner": as_optional_str(result.get("mimetype_inner")),
        "download_url": as_optional_str(result.get("url")),
        "state": as_optional_str(result.get("state")),
        "resource_type": as_optional_str(result.get("resource_type")),
        "created": as_optional_str(result.get("created")),
        "last_modified": as_optional_str(result.get("last_modified")),
        "size_bytes": as_optional_int(result.get("size")),
        "position": as_optional_int(result.get("position")),
        "package_id": as_optional_str(result.get("package_id")),
    }


def register_get_resource_tool(mcp: FastMCP) -> None:
    """Register the ``get_resource`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool get_resource")

    @mcp.tool(name="get_resource")
    async def get_resource_tool(
        id: str,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> ResourceDetails:
        """
        Get one resource from Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``resource_show`` and is optimized for
        retrieving a resource's download metadata and package linkage.

        Args:
            id: Resource identifier accepted by CKAN (UUID).
                A common workflow is to pass a value returned by
                ``get_dataset`` in the resource list.
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``ResourceDetails`` with normalized fields such as format,
            mimetype, download URL, and package linkage.
        """

        return await get_resource(
            id=id,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
