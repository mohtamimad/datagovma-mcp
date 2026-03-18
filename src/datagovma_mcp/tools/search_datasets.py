"""Dataset search tool for Morocco Open Data Government (data.gov.ma)."""

from __future__ import annotations

import json
import logging
from typing import TypedDict, cast

import httpx
from mcp.server.fastmcp import FastMCP

from datagovma_mcp.utils.ckan import (
    DEFAULT_API_BASE_URL,
    CKANAPIError,
    as_str_object_dict,
    fetch_ckan_result,
)
from datagovma_mcp.utils.normalizers import as_optional_str
from datagovma_mcp.utils.validators import is_int, validate_non_negative_int

logger = logging.getLogger(__name__)


class DatasetSearchResult(TypedDict):
    """Normalized payload shape returned by ``search_datasets``."""

    api_base_url: str
    search_url: str
    query: str | None
    filter_query: str | None
    rows: int
    start: int
    sort: str | None
    sort_applied: str | None
    count: int
    returned: int
    results: list[dict[str, object]]
    facets: dict[str, dict[str, int]]
    search_facets: dict[str, object]


def _normalize_optional_string(value: str | None, *, field_name: str) -> str | None:
    """Return a stripped string or ``None`` for empty/omitted values."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"`{field_name}` must be a string")
    normalized = value.strip()
    return normalized or None


def _normalize_facet_fields(facet_fields: list[str] | None) -> list[str]:
    """Validate facet fields and return an ordered, de-duplicated list."""

    if facet_fields is None:
        return []
    if not isinstance(facet_fields, list):
        raise ValueError("`facet_fields` must be a list of strings")

    normalized: list[str] = []
    seen: set[str] = set()
    for item in facet_fields:
        if not isinstance(item, str):
            raise ValueError("`facet_fields` must contain only strings")
        field_name = item.strip()
        if not field_name:
            raise ValueError("`facet_fields` cannot contain empty values")
        if field_name not in seen:
            normalized.append(field_name)
            seen.add(field_name)
    return normalized


def _normalize_facets(value: object) -> dict[str, dict[str, int]]:
    """Normalize CKAN ``facets`` into a stable string-to-int mapping."""

    if not isinstance(value, dict):
        return {}

    normalized_facets: dict[str, dict[str, int]] = {}
    for facet_name, raw_counts in value.items():
        if not isinstance(facet_name, str) or not isinstance(raw_counts, dict):
            continue

        facet_counts: dict[str, int] = {}
        for term, count in raw_counts.items():
            if isinstance(term, str) and is_int(count):
                facet_counts[term] = count
        normalized_facets[facet_name] = facet_counts
    return normalized_facets


def _normalize_search_facets(value: object) -> dict[str, object]:
    """Normalize CKAN ``search_facets`` to a dictionary with string keys."""

    if not isinstance(value, dict):
        return {}

    normalized: dict[str, object] = {}
    for key, facet_value in value.items():
        if isinstance(key, str):
            normalized[key] = facet_value
    return normalized


async def search_datasets(
    q: str | None = None,
    fq: str | None = None,
    rows: int = 10,
    start: int = 0,
    sort: str | None = None,
    facet_fields: list[str] | None = None,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> DatasetSearchResult:
    """
    Search datasets from CKAN ``package_search`` with validated inputs.

    Args:
        q: Full-text search query (example: ``"budget"``).
        fq: Optional CKAN filter query string
            (example: ``"organization:ministry-of-finance"``).
        rows: Number of rows requested (``0`` allowed for count-only queries;
            example: ``10``).
        start: Zero-based pagination offset (example: ``0`` for first page,
            ``10`` for next page when ``rows=10``).
        sort: Optional CKAN sort expression
            (example: ``"metadata_modified desc"``).
        facet_fields: Optional facet field names to aggregate
            (example: ``["organization", "tags"]``).
        api_base_url: CKAN Action API base URL
            (example: ``"https://data.gov.ma/data/api/3/action"``).
        timeout_seconds: Upstream request timeout in seconds (example: ``15.0``).
        verify_ssl: Whether to validate HTTPS certificates for the upstream call
            (example: ``True``).

    Returns:
        A normalized payload with stable keys including request parameters,
        pagination values, dataset results, and facet metadata.

    Raises:
        ValueError: If input parameters fail validation.
        CKANAPIError: If the request fails, times out, returns non-JSON data,
            returns ``success: false``, or has an invalid CKAN envelope.
    """

    normalized_q = _normalize_optional_string(q, field_name="q")
    normalized_fq = _normalize_optional_string(fq, field_name="fq")
    normalized_sort = _normalize_optional_string(sort, field_name="sort")
    normalized_rows = validate_non_negative_int(rows, field_name="rows")
    normalized_start = validate_non_negative_int(start, field_name="start")
    normalized_facet_fields = _normalize_facet_fields(facet_fields)
    logger.info(
        "Searching datasets from %s q=%r fq=%r rows=%s start=%s sort=%r facets=%s",
        api_base_url,
        normalized_q,
        normalized_fq,
        normalized_rows,
        normalized_start,
        normalized_sort,
        len(normalized_facet_fields),
    )

    query_params: dict[str, str | int] = {
        "rows": normalized_rows,
        "start": normalized_start,
    }
    if normalized_q is not None:
        query_params["q"] = normalized_q
    if normalized_fq is not None:
        query_params["fq"] = normalized_fq
    if normalized_sort is not None:
        query_params["sort"] = normalized_sort
    if normalized_facet_fields:
        query_params["facet"] = "true"
        # CKAN expects ``facet.field`` as a JSON-encoded list string.
        query_params["facet.field"] = json.dumps(normalized_facet_fields)

    search_url, result = await fetch_ckan_result(
        api_base_url=api_base_url,
        action_name="package_search",
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
        query_params=query_params,
        client_factory=httpx.AsyncClient,
    )

    count = result.get("count")
    if not is_int(count):
        raise CKANAPIError("Malformed CKAN response: `result.count` must be an integer")
    count_value = cast(int, count)

    raw_results = result.get("results")
    if not isinstance(raw_results, list):
        raise CKANAPIError("Malformed CKAN response: `result.results` must be a list")

    normalized_results: list[dict[str, object]] = []
    for index, item in enumerate(raw_results):
        normalized_results.append(as_str_object_dict(item, field_name=f"result.results[{index}]"))
    logger.info(
        "Dataset search completed from %s count=%s returned=%s",
        search_url,
        count_value,
        len(normalized_results),
    )

    return {
        "api_base_url": api_base_url,
        "search_url": search_url,
        "query": normalized_q,
        "filter_query": normalized_fq,
        "rows": normalized_rows,
        "start": normalized_start,
        "sort": normalized_sort,
        "sort_applied": as_optional_str(result.get("sort")),
        "count": count_value,
        "returned": len(normalized_results),
        "results": normalized_results,
        "facets": _normalize_facets(result.get("facets")),
        "search_facets": _normalize_search_facets(result.get("search_facets")),
    }


def register_search_datasets_tool(mcp: FastMCP) -> None:
    """Register the ``search_datasets`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool search_datasets")

    @mcp.tool(name="search_datasets")
    async def search_datasets_tool(
        q: str | None = None,
        fq: str | None = None,
        rows: int = 10,
        start: int = 0,
        sort: str | None = None,
        facet_fields: list[str] | None = None,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> DatasetSearchResult:
        """
        Search datasets on Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``package_search`` and is optimized for
        open-data discovery, paging, and facet exploration on the Moroccan
        government open data portal.

        Args:
            q: Full-text query string over dataset metadata
                (example: ``"budget"``).
            fq: Optional CKAN filter query string
                (example: ``"organization:ministry-of-finance"``).
            rows: Number of datasets requested (example: ``10``).
            start: Zero-based pagination offset (example: ``0``).
            sort: Optional CKAN sort expression
                (example: ``"metadata_modified desc"``).
            facet_fields: Optional facet field names
                (example: ``["organization", "tags"]``).
            api_base_url: CKAN Action API base URL
                (example: ``"https://data.gov.ma/data/api/3/action"``).
            timeout_seconds: Upstream request timeout in seconds (example: ``15.0``).
            verify_ssl: Whether HTTPS certificates must be verified (example: ``True``).

        Returns:
            ``DatasetSearchResult`` including total ``count``, current page
            ``results``, applied pagination/sort metadata, and optional facets.
        """

        return await search_datasets(
            q=q,
            fq=fq,
            rows=rows,
            start=start,
            sort=sort,
            facet_fields=facet_fields,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
