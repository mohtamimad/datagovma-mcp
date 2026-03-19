"""Shared normalization helpers for common response fields."""

from collections.abc import Sequence
from typing import cast

from datagovma_mcp.utils.validators import is_int


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


def as_optional_int(value: object) -> int | None:
    """Return ``value`` when it is an integer; otherwise return ``None``."""

    if is_int(value):
        return cast(int, value)
    return None


def normalize_optional_string(value: str | None, *, field_name: str) -> str | None:
    """Normalize optional string input by trimming and collapsing blanks to ``None``."""

    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"`{field_name}` must be a string")
    normalized = value.strip()
    return normalized or None


def normalize_facet_fields(
    facet_fields: list[str] | None,
    *,
    default_fields: Sequence[str] | None = None,
) -> list[str]:
    """
    Validate facet fields and return an ordered, de-duplicated list.

    When ``facet_fields`` is ``None``, returns ``default_fields`` when provided,
    otherwise an empty list.
    """

    if facet_fields is None:
        return list(default_fields) if default_fields is not None else []
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
