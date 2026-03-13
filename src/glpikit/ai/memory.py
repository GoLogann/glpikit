"""Helpers to represent GLPI objects for memory/RAG pipelines."""

from __future__ import annotations

import json
from typing import Any

from .prompting import to_llm_context


def as_json_compact(obj: Any) -> str:
    return json.dumps(to_llm_context(obj), ensure_ascii=True, separators=(",", ":"))


def as_text(obj: Any) -> str:
    ctx = to_llm_context(obj)
    if isinstance(ctx, str):
        return ctx
    return json.dumps(ctx, ensure_ascii=False, indent=2)


def as_markdown(obj: Any) -> str:
    ctx = to_llm_context(obj)
    if isinstance(ctx, dict):
        lines = ["# GLPI Context"]
        for key, value in ctx.items():
            lines.append(f"- **{key}**: {value}")
        return "\n".join(lines)
    return f"# GLPI Context\n\n{ctx}"
