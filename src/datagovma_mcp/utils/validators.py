"""Shared input validation helpers."""


def is_int(value: object) -> bool:
    """Return whether ``value`` is an integer (excluding booleans)."""

    return isinstance(value, int) and not isinstance(value, bool)


def validate_non_negative_int(value: int, *, field_name: str) -> int:
    """Validate that ``value`` is an integer greater than or equal to zero."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"`{field_name}` must be an integer")
    if value < 0:
        raise ValueError(f"`{field_name}` must be >= 0")
    return value


def validate_non_empty_str(value: str, *, field_name: str) -> str:
    """Validate that ``value`` is a non-empty string after trimming."""

    if not isinstance(value, str):
        raise ValueError(f"`{field_name}` must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"`{field_name}` cannot be empty")
    return normalized
