"""Shared CKAN helpers used by multiple MCP tools."""

from __future__ import annotations

import json
import logging
import ssl
from collections.abc import Callable
from typing import Any

import httpx

DEFAULT_API_BASE_URL = "https://data.gov.ma/data/api/3/action"
logger = logging.getLogger(__name__)


class CKANAPIError(RuntimeError):
    """Raised when a CKAN action request cannot be fetched or validated."""


def build_action_url(api_base_url: str, action_name: str) -> str:
    """Build a CKAN action endpoint URL from the API base URL and action name."""

    return f"{api_base_url.rstrip('/')}/{action_name}"


def as_optional_str(value: object) -> str | None:
    """Return ``value`` when it is a string; otherwise return ``None``."""

    if isinstance(value, str):
        return value
    return None


def as_string_list(value: object) -> list[str]:
    """Return a list containing only string items from a list-like field."""

    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def is_int(value: object) -> bool:
    """Return whether ``value`` is an integer (excluding booleans)."""

    return isinstance(value, int) and not isinstance(value, bool)


def as_str_object_dict(value: object, *, field_name: str) -> dict[str, object]:
    """Validate that ``value`` is a dictionary with string keys."""

    if not isinstance(value, dict):
        raise CKANAPIError(f"Malformed CKAN response: `{field_name}` must be an object")

    normalized: dict[str, object] = {}
    for key, field_value in value.items():
        if not isinstance(key, str):
            raise CKANAPIError(f"Malformed CKAN response: `{field_name}` keys must be strings")
        normalized[key] = field_value
    return normalized


async def fetch_ckan_result(
    *,
    api_base_url: str,
    action_name: str,
    timeout_seconds: float,
    verify_ssl: bool,
    query_params: dict[str, str | int] | None = None,
    client_factory: Callable[..., Any] = httpx.AsyncClient,
) -> tuple[str, dict[str, object]]:
    """
    Call a CKAN action endpoint and return the validated ``result`` object.

    Returns:
        Tuple of ``(action_url, result_dict)``.
    """

    if timeout_seconds <= 0:
        logger.error("Invalid timeout_seconds=%s for action %s", timeout_seconds, action_name)
        raise ValueError("`timeout_seconds` must be > 0")

    action_url = build_action_url(api_base_url, action_name)
    ssl_context: ssl.SSLContext | bool
    ssl_context = True if verify_ssl else ssl._create_unverified_context()
    timeout = httpx.Timeout(timeout_seconds)
    logger.debug(
        "Calling CKAN action %s at %s with params=%s timeout=%ss verify_ssl=%s",
        action_name,
        action_url,
        query_params,
        timeout_seconds,
        verify_ssl,
    )

    try:
        async with client_factory(
            timeout=timeout,
            verify=ssl_context,
            headers={"Accept": "application/json"},
        ) as client:
            if query_params is None:
                response = await client.get(action_url)
            else:
                response = await client.get(action_url, params=query_params)
            response.raise_for_status()
            raw_body = response.text
            logger.debug(
                "CKAN action %s responded with status_code=%s body_bytes=%s",
                action_name,
                response.status_code,
                len(raw_body),
            )
    except httpx.TimeoutException as exc:
        logger.error("CKAN action %s timed out at %s", action_name, action_url)
        raise CKANAPIError(f"Request timed out for {action_url}") from exc
    except httpx.HTTPError as exc:
        logger.error("CKAN action %s request failed at %s: %s", action_name, action_url, exc)
        raise CKANAPIError(f"Request failed for {action_url}: {exc}") from exc

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        logger.error("CKAN action %s returned non-JSON data at %s", action_name, action_url)
        raise CKANAPIError(f"{action_name} returned non-JSON data") from exc

    if not isinstance(payload, dict):
        logger.error(
            "CKAN action %s returned malformed payload root type=%s",
            action_name,
            type(payload),
        )
        raise CKANAPIError("Malformed CKAN response: root payload must be an object")

    if payload.get("success") is not True:
        # CKAN can return HTTP 200 for application-level failures,
        # so we must enforce the envelope's ``success`` flag explicitly.
        logger.error(
            "CKAN action %s failed with success=false error=%s",
            action_name,
            payload.get("error"),
        )
        raise CKANAPIError(f"CKAN API error in {action_name}: {payload.get('error')}")

    result = as_str_object_dict(payload.get("result"), field_name="result")
    logger.debug("CKAN action %s succeeded", action_name)
    return action_url, result
