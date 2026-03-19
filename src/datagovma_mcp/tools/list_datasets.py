"""Dataset listing tool for Morocco Open Data Government (data.gov.ma)."""

from __future__ import annotations

import logging
from typing import TypedDict

from mcp.server.fastmcp import FastMCP

from datagovma_mcp.utils.ckan import (
    DEFAULT_API_BASE_URL,
    CKANAPIError,
    fetch_ckan_action_result,
)
from datagovma_mcp.utils.validators import validate_non_negative_int

__all__ = ["CKANAPIError", "list_datasets", "register_list_datasets_tool"]
logger = logging.getLogger(__name__)


class DatasetListResult(TypedDict):
    """Normalized payload shape returned by ``list_datasets``."""

    api_base_url: str
    list_url: str
    limit: int
    offset: int
    returned: int
    datasets: list[str]


def _normalize_dataset_names(value: object) -> list[str]:
    """Validate and return dataset names from CKAN ``package_list``."""

    if not isinstance(value, list):
        raise CKANAPIError("Malformed CKAN response: `result` must be a list")

    dataset_names: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise CKANAPIError(f"Malformed CKAN response: `result[{index}]` must be a string")
        dataset_names.append(item)
    return dataset_names


async def list_datasets(
    limit: int = 100,
    offset: int = 0,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> DatasetListResult:
    """
    List dataset names from CKAN ``package_list`` with pagination support.

    Args:
        limit: Number of dataset names requested (example: ``100``).
            CKAN ``package_list`` treats ``0`` as unbounded on many portals,
            including ``data.gov.ma`` (for example: ``limit=0`` returns all
            names from the provided ``offset``).
        offset: Zero-based pagination offset (example: ``0`` for first page).
        api_base_url: CKAN Action API base URL
            (example: ``"https://data.gov.ma/data/api/3/action"``).
        timeout_seconds: Upstream request timeout in seconds (example: ``15.0``).
        verify_ssl: Whether to validate HTTPS certificates for the upstream call
            (example: ``True``).

    Returns:
        A normalized payload with requested pagination values and dataset names.

    Raises:
        ValueError: If input parameters fail validation.
        CKANAPIError: If the request fails, times out, returns non-JSON data,
            returns ``success: false``, or has an invalid CKAN envelope.
    """

    normalized_limit = validate_non_negative_int(limit, field_name="limit")
    normalized_offset = validate_non_negative_int(offset, field_name="offset")
    logger.info(
        "Listing datasets from %s limit=%s offset=%s",
        api_base_url,
        normalized_limit,
        normalized_offset,
    )

    list_url, raw_result = await fetch_ckan_action_result(
        api_base_url=api_base_url,
        action_name="package_list",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        query_params={"limit": normalized_limit, "offset": normalized_offset},
    )
    datasets = _normalize_dataset_names(raw_result)
    logger.info("Dataset list fetched from %s returned=%s", list_url, len(datasets))

    return {
        "api_base_url": api_base_url,
        "list_url": list_url,
        "limit": normalized_limit,
        "offset": normalized_offset,
        "returned": len(datasets),
        "datasets": datasets,
    }


def register_list_datasets_tool(mcp: FastMCP) -> None:
    """Register the ``list_datasets`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool list_datasets")

    @mcp.tool(name="list_datasets")
    async def list_datasets_tool(
        limit: int = 100,
        offset: int = 0,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> DatasetListResult:
        """
        List dataset names from Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``package_list`` and is optimized for lightweight
        dataset enumeration with explicit paging controls.

        Args:
            limit: Number of dataset names requested (example: ``100``).
                Note: CKAN ``package_list`` accepts ``limit=0`` as an
                unbounded request on this portal, returning all names from the
                requested ``offset``.
            offset: Zero-based pagination offset (example: ``0``).
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``DatasetListResult`` with pagination metadata and dataset names.
        """

        return await list_datasets(
            limit=limit,
            offset=offset,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
