"""Search and filter payload helpers."""

from __future__ import annotations

from typing import Any


def normalize_sort(order: str | None) -> str | None:
    if order is None:
        return None
    normalized = order.lower()
    if normalized not in {"asc", "desc"}:
        raise ValueError("sort order must be 'asc' or 'desc'")
    return normalized


def compact_dict(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}
