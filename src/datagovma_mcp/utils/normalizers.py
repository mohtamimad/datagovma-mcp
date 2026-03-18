"""Shared normalization helpers for common response fields."""


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
