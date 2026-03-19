"""Organization detail tool for Morocco Open Data Government (data.gov.ma)."""

from __future__ import annotations

import logging
from typing import TypedDict

from mcp.server.fastmcp import FastMCP

from datagovma_mcp.utils.ckan import (
    DEFAULT_API_BASE_URL,
    CKANAPIError,
    as_str_object_dict,
    fetch_ckan_result,
)
from datagovma_mcp.utils.normalizers import as_optional_int, as_optional_str
from datagovma_mcp.utils.validators import validate_non_empty_str

__all__ = ["CKANAPIError", "get_organization", "register_get_organization_tool"]
logger = logging.getLogger(__name__)


class OrganizationDetails(TypedDict):
    """Normalized payload shape returned by ``get_organization``."""

    api_base_url: str
    organization_show_url: str
    requested_id: str
    include_datasets: bool
    id: str | None
    name: str | None
    title: str | None
    description: str | None
    state: str | None
    organization_type: str | None
    created: str | None
    image_url: str | None
    package_count: int | None
    dataset_count: int
    datasets: list[dict[str, object]]


def _validate_bool(value: bool, *, field_name: str) -> bool:
    """Validate that ``value`` is a boolean."""

    if not isinstance(value, bool):
        raise ValueError(f"`{field_name}` must be a boolean")
    return value


async def get_organization(
    id: str,
    include_datasets: bool = False,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> OrganizationDetails:
    """
    Fetch and normalize a single organization from CKAN ``organization_show``.

    Args:
        id: Organization identifier accepted by CKAN (name/slug or UUID).
        include_datasets: Whether the response should include linked dataset
            objects in ``result.packages``.
        api_base_url: CKAN Action API base URL.
        timeout_seconds: Upstream request timeout in seconds.
        verify_ssl: Whether to validate HTTPS certificates for the upstream call.

    Returns:
        A normalized payload with organization metadata and optional datasets.

    Raises:
        ValueError: If ``id`` is not a non-empty string or
            ``include_datasets`` is not a boolean.
        CKANAPIError: If the request fails, times out, returns non-JSON data,
            returns ``success: false``, or has an invalid CKAN envelope.
    """

    normalized_id = validate_non_empty_str(id, field_name="id")
    normalized_include_datasets = _validate_bool(
        include_datasets,
        field_name="include_datasets",
    )
    logger.info(
        "Fetching organization id=%s from %s include_datasets=%s",
        normalized_id,
        api_base_url,
        normalized_include_datasets,
    )

    organization_show_url, result = await fetch_ckan_result(
        api_base_url=api_base_url,
        action_name="organization_show",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        query_params={
            "id": normalized_id,
            "include_datasets": "true" if normalized_include_datasets else "false",
        },
    )

    raw_packages = result.get("packages")
    if raw_packages is None:
        datasets: list[dict[str, object]] = []
    elif not isinstance(raw_packages, list):
        raise CKANAPIError("Malformed CKAN response: `result.packages` must be a list")
    else:
        datasets = []
        for index, item in enumerate(raw_packages):
            datasets.append(as_str_object_dict(item, field_name=f"result.packages[{index}]"))

    logger.info(
        "Organization fetched from %s id=%s package_count=%s datasets=%s",
        organization_show_url,
        normalized_id,
        as_optional_int(result.get("package_count")),
        len(datasets),
    )

    return {
        "api_base_url": api_base_url,
        "organization_show_url": organization_show_url,
        "requested_id": normalized_id,
        "include_datasets": normalized_include_datasets,
        "id": as_optional_str(result.get("id")),
        "name": as_optional_str(result.get("name")),
        "title": as_optional_str(result.get("title")),
        "description": as_optional_str(result.get("description")),
        "state": as_optional_str(result.get("state")),
        "organization_type": as_optional_str(result.get("type")),
        "created": as_optional_str(result.get("created")),
        "image_url": as_optional_str(result.get("image_url")),
        "package_count": as_optional_int(result.get("package_count")),
        "dataset_count": len(datasets),
        "datasets": datasets,
    }


def register_get_organization_tool(mcp: FastMCP) -> None:
    """Register the ``get_organization`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool get_organization")

    @mcp.tool(name="get_organization")
    async def get_organization_tool(
        id: str,
        include_datasets: bool = False,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> OrganizationDetails:
        """
        Get one organization from Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``organization_show`` and is optimized for
        retrieving organization metadata, with optional dataset expansion.

        Args:
            id: Organization identifier accepted by CKAN (name/slug or UUID).
                A common workflow is to pass a value returned by
                ``list_organizations``.
            include_datasets: Whether to include linked dataset objects.
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``OrganizationDetails`` with normalized organization fields and an
            optional ``datasets`` payload.
        """

        return await get_organization(
            id=id,
            include_datasets=include_datasets,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
