"""Shared normalization helpers for common response fields."""

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
