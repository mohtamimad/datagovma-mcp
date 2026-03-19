"""Dataset facets tool for Morocco Open Data Government (data.gov.ma)."""

from __future__ import annotations

import logging
from typing import TypedDict

from mcp.server.fastmcp import FastMCP

from datagovma_mcp.tools.search_datasets import search_datasets
from datagovma_mcp.utils.ckan import DEFAULT_API_BASE_URL, CKANAPIError
from datagovma_mcp.utils.normalizers import normalize_facet_fields

__all__ = ["CKANAPIError", "get_dataset_facets", "register_get_dataset_facets_tool"]
logger = logging.getLogger(__name__)

DEFAULT_FACET_FIELDS = ("tags", "groups", "organization")


class DatasetFacetsResult(TypedDict):
    """Normalized payload shape returned by ``get_dataset_facets``."""

    api_base_url: str
    search_url: str
    query: str | None
    filter_query: str | None
    facet_fields: list[str]
    facet_field_count: int
    total_count: int
    facets: dict[str, dict[str, int]]
    search_facets: dict[str, object]


async def get_dataset_facets(
    q: str | None = None,
    fq: str | None = None,
    facet_fields: list[str] | None = None,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> DatasetFacetsResult:
    """
    Fetch dataset facet buckets via CKAN ``package_search`` with ``rows=0``.

    This is a practical replacement for CKAN ``tag_list`` on portals where
    tag listing is incomplete but search facets remain available. The tool is
    optimized for discovery analytics (facet distributions) without returning
    full dataset rows.

    Args:
        q: Optional full-text query over dataset metadata
            (example: ``"budget"``).
        fq: Optional CKAN filter query string.
            (example: ``"organization:ministry-of-finance"``).
        facet_fields: Facet fields to aggregate; defaults to
            ``["tags", "groups", "organization"]`` when omitted.
        api_base_url: CKAN Action API base URL
            (example: ``"https://data.gov.ma/data/api/3/action"``).
        timeout_seconds: Upstream request timeout in seconds (example: ``15.0``).
        verify_ssl: Whether to validate HTTPS certificates for the upstream call
            (example: ``True``).

    Returns:
        A normalized payload with:
        - applied request context (query/filter/facet fields),
        - ``total_count`` for matching datasets,
        - ``facets`` and ``search_facets`` distributions,
        - resolved CKAN ``search_url`` metadata.

    Raises:
        ValueError: If input parameters fail validation.
        CKANAPIError: If the upstream CKAN request or envelope validation fails.
    """

    normalized_facet_fields = normalize_facet_fields(
        facet_fields,
        default_fields=DEFAULT_FACET_FIELDS,
    )
    logger.info(
        "Fetching dataset facets from %s q=%r fq=%r facet_fields=%s",
        api_base_url,
        q,
        fq,
        len(normalized_facet_fields),
    )

    search_result = await search_datasets(
        q=q,
        fq=fq,
        rows=0,
        start=0,
        sort=None,
        facet_fields=normalized_facet_fields,
        api_base_url=api_base_url,
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
    )

    logger.info(
        "Dataset facets fetched from %s total_count=%s facet_fields=%s",
        search_result["search_url"],
        search_result["total_count"],
        len(normalized_facet_fields),
    )

    return {
        "api_base_url": search_result["api_base_url"],
        "search_url": search_result["search_url"],
        "query": search_result["query"],
        "filter_query": search_result["filter_query"],
        "facet_fields": normalized_facet_fields,
        "facet_field_count": len(normalized_facet_fields),
        "total_count": search_result["total_count"],
        "facets": search_result["facets"],
        "search_facets": search_result["search_facets"],
    }


def register_get_dataset_facets_tool(mcp: FastMCP) -> None:
    """Register the ``get_dataset_facets`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool get_dataset_facets")

    @mcp.tool(name="get_dataset_facets")
    async def get_dataset_facets_tool(
        q: str | None = None,
        fq: str | None = None,
        facet_fields: list[str] | None = None,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> DatasetFacetsResult:
        """
        Get dataset facet buckets from Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``package_search`` with ``rows=0`` and requested
        ``facet.field`` values to provide practical tag/group/organization
        distributions for discovery workflows where only aggregate metadata is
        needed (no dataset rows).

        Args:
            q: Optional full-text query string over dataset metadata
                (example: ``"budget"``).
            fq: Optional CKAN filter query string
                (example: ``"organization:ministry-of-finance"``).
            facet_fields: Optional facet field names
                (default: ``["tags", "groups", "organization"]``).
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``DatasetFacetsResult`` with ``total_count`` plus ``facets`` and
            ``search_facets`` buckets keyed by requested facet fields.
        """

        return await get_dataset_facets(
            q=q,
            fq=fq,
            facet_fields=facet_fields,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
