"""Safety utilities for agentic operations."""

from __future__ import annotations

from typing import Any


def whitelist_payload(payload: dict[str, Any], allowed_fields: set[str]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if k in allowed_fields}


def diff_payload(current: dict[str, Any], updated: dict[str, Any]) -> dict[str, dict[str, Any]]:
    changed: dict[str, dict[str, Any]] = {}
    keys = set(current) | set(updated)
    for key in keys:
        before = current.get(key)
        after = updated.get(key)
        if before != after:
            changed[key] = {"before": before, "after": after}
    return changed


def require_confirmation(action: str, *, confirmed: bool) -> None:
    if not confirmed:
        raise PermissionError(f"action '{action}' requires confirmation")
