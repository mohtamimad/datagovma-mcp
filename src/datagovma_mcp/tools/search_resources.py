"""Resource search tool for Morocco Open Data Government (data.gov.ma)."""

from __future__ import annotations

import logging
import re
from typing import TypedDict, cast

from mcp.server.fastmcp import FastMCP

from datagovma_mcp.utils.ckan import (
    DEFAULT_API_BASE_URL,
    CKANAPIError,
    as_str_object_dict,
    fetch_ckan_result,
)
from datagovma_mcp.utils.normalizers import as_optional_str, normalize_optional_string
from datagovma_mcp.utils.validators import is_int, validate_non_empty_str, validate_non_negative_int

__all__ = ["CKANAPIError", "search_resources", "register_search_resources_tool"]
logger = logging.getLogger(__name__)

FIELD_VALUE_PATTERN = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*:\s*(.+?)\s*$")


class ResourceSearchResult(TypedDict):
    """Normalized payload shape returned by ``search_resources``."""

    api_base_url: str
    search_url: str
    query: str
    field: str
    value: str
    limit: int
    offset: int
    sort: str | None
    sort_applied: str | None
    total_count: int
    resource_count: int
    resources: list[dict[str, object]]


def _parse_field_value_query(query: str) -> tuple[str, str]:
    """Validate and parse a strict CKAN ``field:value`` query."""

    normalized_query = validate_non_empty_str(query, field_name="query")
    match = FIELD_VALUE_PATTERN.fullmatch(normalized_query)
    if match is None:
        logger.error("Invalid resource search query format query=%r", query)
        raise ValueError("`query` must use CKAN field:value format (example: `name:budget`)")

    field = match.group(1)
    value = match.group(2).strip()
    if not value:
        logger.error("Invalid resource search query value query=%r", query)
        raise ValueError("`query` must include a non-empty value after `:`")
    return field, value


async def search_resources(
    query: str,
    limit: int = 10,
    offset: int = 0,
    sort: str | None = None,
    *,
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> ResourceSearchResult:
    """
    Search resources from CKAN ``resource_search`` with guarded query validation.

    Args:
        query: CKAN search expression in strict ``field:value`` format
            (example: ``"name:stat"``).
        limit: Number of resources requested per page (example: ``10``).
        offset: Zero-based pagination offset (example: ``0``).
        sort: Optional sort expression mapped to CKAN ``order_by``
            (example: ``"last_modified desc"``).
        api_base_url: CKAN Action API base URL.
        timeout_seconds: Upstream request timeout in seconds.
        verify_ssl: Whether to validate HTTPS certificates for the upstream call.

    Returns:
        A normalized payload containing requested query/pagination metadata and
        resource results.

    Raises:
        ValueError: If inputs fail validation (including non ``field:value`` query).
        CKANAPIError: If the request fails, times out, returns invalid CKAN
            envelope data, or appears blocked by upstream WAF.
    """

    field, value = _parse_field_value_query(query)
    normalized_query = f"{field}:{value}"
    normalized_limit = validate_non_negative_int(limit, field_name="limit")
    normalized_offset = validate_non_negative_int(offset, field_name="offset")
    normalized_sort = normalize_optional_string(sort, field_name="sort")
    logger.info(
        "Searching resources from %s query=%r limit=%s offset=%s sort=%r",
        api_base_url,
        normalized_query,
        normalized_limit,
        normalized_offset,
        normalized_sort,
    )

    query_params: dict[str, str | int] = {
        "query": normalized_query,
        "limit": normalized_limit,
        "offset": normalized_offset,
    }
    if normalized_sort is not None:
        query_params["order_by"] = normalized_sort

    try:
        search_url, result = await fetch_ckan_result(
            api_base_url=api_base_url,
            action_name="resource_search",
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
            query_params=query_params,
        )
    except CKANAPIError as exc:
        if "resource_search returned non-JSON data" in str(exc):
            logger.error(
                "Resource search likely blocked by WAF query=%r api_base_url=%s",
                normalized_query,
                api_base_url,
            )
            raise CKANAPIError(
                "resource_search appears blocked by upstream WAF; use strict "
                "`field:value` queries (example: `name:budget`)."
            ) from exc
        logger.error(
            "Resource search failed query=%r api_base_url=%s error=%s",
            normalized_query,
            api_base_url,
            exc,
        )
        raise

    count = result.get("count")
    if not is_int(count):
        logger.error(
            "Malformed resource_search response at %s: invalid result.count type=%s",
            search_url,
            type(count).__name__,
        )
        raise CKANAPIError("Malformed CKAN response: `result.count` must be an integer")
    count_value = cast(int, count)

    raw_results = result.get("results")
    if not isinstance(raw_results, list):
        logger.error(
            "Malformed resource_search response at %s: invalid result.results type=%s",
            search_url,
            type(raw_results).__name__,
        )
        raise CKANAPIError("Malformed CKAN response: `result.results` must be a list")

    resources: list[dict[str, object]] = []
    for index, item in enumerate(raw_results):
        resources.append(as_str_object_dict(item, field_name=f"result.results[{index}]"))
    logger.info(
        "Resource search completed from %s total_count=%s resource_count=%s",
        search_url,
        count_value,
        len(resources),
    )

    return {
        "api_base_url": api_base_url,
        "search_url": search_url,
        "query": normalized_query,
        "field": field,
        "value": value,
        "limit": normalized_limit,
        "offset": normalized_offset,
        "sort": normalized_sort,
        "sort_applied": as_optional_str(result.get("sort")),
        "total_count": count_value,
        "resource_count": len(resources),
        "resources": resources,
    }


def register_search_resources_tool(mcp: FastMCP) -> None:
    """Register the ``search_resources`` tool for Morocco's open data portal."""
    logger.debug("Registering MCP tool search_resources")

    @mcp.tool(name="search_resources")
    async def search_resources_tool(
        query: str,
        limit: int = 10,
        offset: int = 0,
        sort: str | None = None,
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> ResourceSearchResult:
        """
        Search resources on Morocco Open Data Government (``data.gov.ma``).

        This tool wraps CKAN ``resource_search`` with strict ``field:value``
        query validation to reduce WAF-triggering query patterns while still
        supporting filtered resource discovery.

        Args:
            query: CKAN ``field:value`` expression
                (example: ``"name:stat"``).
            limit: Number of resources requested (example: ``10``).
            offset: Zero-based pagination offset (example: ``0``).
            sort: Optional sort expression mapped to CKAN ``order_by``.
            api_base_url: CKAN Action API base URL for the target portal
                (default points to Morocco open data: data.gov.ma).
            timeout_seconds: Upstream request timeout in seconds for CKAN.
            verify_ssl: Whether HTTPS certificates must be verified.

        Returns:
            ``ResourceSearchResult`` including query metadata, paging fields,
            and normalized resource rows.
        """

        return await search_resources(
            query=query,
            limit=limit,
            offset=offset,
            sort=sort,
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
