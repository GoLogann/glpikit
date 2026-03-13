"""Prompt context helpers."""

from __future__ import annotations

from typing import Any


def to_llm_context(obj: Any) -> dict[str, Any] | list[Any] | str:
    if hasattr(obj, "to_llm_context"):
        return obj.to_llm_context()
    if hasattr(obj, "model_dump"):
        return obj.model_dump(exclude_none=True)
    return str(obj)
