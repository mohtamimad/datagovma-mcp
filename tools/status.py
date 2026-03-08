"""Status tool for the Moroccan Open Data CKAN API."""

from __future__ import annotations

import json
import ssl
from typing import TypedDict

import httpx
from mcp.server.fastmcp import FastMCP

DEFAULT_API_BASE_URL = "https://data.gov.ma/data/api/3/action"


class CKANAPIError(RuntimeError):
    """Raised when the CKAN API call fails or returns invalid data."""


class PortalStatus(TypedDict):
    """Normalized status payload returned by ``get_portal_status``."""

    api_base_url: str
    status_url: str
    site_title: str | None
    site_description: str | None
    site_url: str | None
    ckan_version: str | None
    locale_default: str | None
    extensions: list[str]


def _build_status_url(api_base_url: str) -> str:
    return f"{api_base_url.rstrip('/')}/status_show"


def _as_optional_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


async def get_portal_status(
    api_base_url: str = DEFAULT_API_BASE_URL,
    timeout_seconds: float = 15.0,
    verify_ssl: bool = True,
) -> PortalStatus:
    """
    Fetch and normalize portal status metadata from CKAN ``status_show``.

    Args:
        api_base_url: CKAN Action API base URL.
        timeout_seconds: Request timeout in seconds.
        verify_ssl: Whether SSL certificates must be verified.

    Returns:
        A normalized status payload with stable keys:
        - ``api_base_url``: Base CKAN Action API URL used for the request.
        - ``status_url``: Resolved ``status_show`` endpoint URL called.
        - ``site_title``: Portal title from CKAN settings.
        - ``site_description``: Portal description from CKAN settings.
        - ``site_url``: Public portal root URL.
        - ``ckan_version``: CKAN server version string.
        - ``locale_default``: Default portal locale code.
        - ``extensions``: Enabled CKAN extension names.

    Raises:
        CKANAPIError: On transport errors, invalid JSON, API errors, or
            malformed response envelopes.
    """

    status_url = _build_status_url(api_base_url)
    ssl_context: ssl.SSLContext | bool
    ssl_context = True if verify_ssl else ssl._create_unverified_context()
    timeout = httpx.Timeout(timeout_seconds)

    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            verify=ssl_context,
            headers={"Accept": "application/json"},
        ) as client:
            response = await client.get(status_url)
            response.raise_for_status()
            raw_body = response.text
    except httpx.TimeoutException as exc:
        raise CKANAPIError(f"Request timed out for {status_url}") from exc
    except httpx.HTTPError as exc:
        raise CKANAPIError(f"Request failed for {status_url}: {exc}") from exc

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise CKANAPIError("status_show returned non-JSON data") from exc

    if not isinstance(payload, dict):
        raise CKANAPIError("Malformed CKAN response: root payload must be an object")

    if payload.get("success") is not True:
        raise CKANAPIError(f"CKAN API error in status_show: {payload.get('error')}")

    result = payload.get("result")
    if not isinstance(result, dict):
        raise CKANAPIError("Malformed CKAN response: `result` must be an object")

    extensions = _as_string_list(result.get("extensions"))

    return {
        "api_base_url": api_base_url,
        "status_url": status_url,
        "site_title": _as_optional_str(result.get("site_title")),
        "site_description": _as_optional_str(result.get("site_description")),
        "site_url": _as_optional_str(result.get("site_url")),
        "ckan_version": _as_optional_str(result.get("ckan_version")),
        "locale_default": _as_optional_str(result.get("locale_default")),
        "extensions": extensions,
    }


def register_status_tool(mcp: FastMCP) -> None:
    """Register the status MCP tool."""

    @mcp.tool(name="get_portal_status")
    async def get_portal_status_tool(
        api_base_url: str = DEFAULT_API_BASE_URL,
        timeout_seconds: float = 15.0,
        verify_ssl: bool = True,
    ) -> PortalStatus:
        """
        Return metadata about the Moroccan Open Data CKAN portal.

        Args:
            api_base_url: CKAN Action API base URL.
            timeout_seconds: Upstream request timeout in seconds.
            verify_ssl: Whether HTTPS certificates must be verified.
        """

        return await get_portal_status(
            api_base_url=api_base_url,
            timeout_seconds=timeout_seconds,
            verify_ssl=verify_ssl,
        )
