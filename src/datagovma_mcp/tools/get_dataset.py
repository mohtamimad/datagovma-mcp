"""Dataset detail tool for Morocco Open Data Government (data.gov.ma)."""

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
from datagovma_mcp.utils.normalizers import as_optional_str
from datagovma_mcp.utils.validators import validate_non_empty_str

__all__ = ["CKANAPIError", "get_dataset", "register_get_dataset_tool"]
logger = logging.getLogger(__name__)


class DatasetDetails(TypedDict):
    """Normalized payload shape returned by ``get_dataset``."""

    api_base_url: str
    dataset_url: str
    requested_id: str
    id: str | None
    name: str | None
    title: str | None
    notes: str | None
    state: str | None
    private: bool | None
    metadata_created: str | None
    metadata_modified: str | None
    organization_name: str | None
    organization_title: str | None
    tags: list[str]
    groups: list[str]
    resource_count: int
    resources: list[dict[str, object]]


def _as_optional_bool(value: object) -> bool | None:
    """Return ``value`` when it is a boolean; otherwise return ``None``."""

    if isinstance(value, bool):
        return value
    return None


def _normalize_named_items(value: object, *, field_name: str) -> list[str]:
    """Extract a ``name`` list from CKAN objects like tags and groups."""

    if not isinstance(value, list):
        return []

    names: list[str] = []
    for index, item in enumerate(value):
        item_dict = as_str_object_dict(item, field_name=f"{field_name}[{index}]")
        name = as_optional_str(item_dict.get("name"))
        if name:
            names.append(name)
    return names


def _normalize_organization(value: object) -> tuple[str | None, str | None]:
    """Return organization name/title when present."""

    if value is None:
        return None, None
    organization = as_str_object_dict(value, field_name="result.organization")
    return as_optional_str(organization.get("name")), as_optional_str(organization.get("title"))


async def get_dataset(
    id: str,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> DatasetDetails:
    """
    Fetch and normalize a single dataset from CKAN ``package_show``.

    Args:
        id: Dataset identifier accepted by CKAN (name/slug or UUID).
        api_base_url: CKAN Action API base URL.
        timeout_seconds: Upstream request timeout in seconds.
        verify_ssl: Whether to validate HTTPS certificates for the upstream call.

    Returns:
        A normalized payload with the requested dataset metadata and resources.

    Raises:
        ValueError: If ``id`` is not a non-empty string.
        CKANAPIError: If the request fails, times out, returns non-JSON data,
            returns ``success: false``, or has an invalid CKAN envelope.
    """

    normalized_id = validate_non_empty_str(id, field_name="id")
    logger.info("Fetching dataset id=%s from %s", normalized_id, api_base_url)

    dataset_url, result = await fetch_ckan_result(
        api_base_url=api_base_url,
        action_name="package_show",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        query_params={"id": normalized_id},
    )

    raw_resources = result.get("resources")
    if not isinstance(raw_resources, list):
        raise CKANAPIError("Malformed CKAN response: `result.resources` must be a list")

    resources: list[dict[str, object]] = []
    for index, item in enumerate(raw_resources):
        resources.append(as_str_object_dict(item, field_name=f"result.resources[{index}]"))

    organization_name, organization_title = _normalize_organization(result.get("organization"))
    logger.info(
        "Dataset fetched from %s id=%s resources=%s organization=%s",
        dataset_url,
        normalized_id,
        len(resources),
        organization_name,
    )

    return {
        "api_base_url": api_base_url,
        "dataset_url": dataset_url,
        "requested_id": normalized_id,
        "id": as_optional_str(result.get("id")),
        "name": as_optional_str(result.get("name")),
        "title": as_optional_str(result.get("title")),
        "notes": as_optional_str(result.get("notes")),
        "state": as_optional_str(result.get("state")),
        "private": _as_optional_bool(result.get("private")),
        "metadata_created": as_optional_str(result.get("metadata_created")),
        "metadata_modified": as_optional_str(result.get("metadata_modified")),
        "organization_name": organization_name,
        "organization_title": organization_title,
        "tags": _normalize_named_items(result.get("tags"), field_name="result.tags"),
        "groups": _normalize_named_items(result.get("groups"), field_name="result.groups"),
        "resource_count": len(resources),
        "resources": resources,
    }


def register_get_dataset_tool(mcp: FastMCP) -> None:
    """Register the ``get_dataset`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool get_dataset")

    @mcp.tool(name="get_dataset")
    async def get_dataset_tool(
        id: str,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> DatasetDetails:
        """
        Get one dataset from Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``package_show`` and is optimized for retrieving
        a single dataset's core metadata and resource list after discovery.

        Args:
            id: Dataset identifier accepted by CKAN (name/slug or UUID).
                A common workflow is to pass a value returned by
                ``search_datasets``.
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``DatasetDetails`` with normalized fields such as title, notes,
            organization, tags/groups, and full resource metadata.
        """

        return await get_dataset(
            id=id,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
