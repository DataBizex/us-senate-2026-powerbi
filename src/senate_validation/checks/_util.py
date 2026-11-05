"""Helpers shared by the check modules."""

from __future__ import annotations

from collections.abc import Iterable

MAX_LISTED = 20


def split_cell(value: str, separator: str | None) -> list[str]:
    """Split a multi-valued cell; blank parts are dropped."""
    if not separator:
        return [value] if value != "" else []
    return [part.strip() for part in value.split(separator) if part.strip() != ""]


def truncate(violations: Iterable[str], limit: int = MAX_LISTED) -> list[str]:
    """Keep failure output readable when a check fails on many rows."""
    items = list(violations)
    if len(items) <= limit:
        return items
    return items[:limit] + [f"... and {len(items) - limit} more"]
