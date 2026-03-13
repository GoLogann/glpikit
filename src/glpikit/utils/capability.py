"""Capability helpers for probing GLPI surfaces."""

from __future__ import annotations

import re
from typing import Any

from glpikit.v2 import infer_itemtypes_from_paths


def extract_plugins(config_payload: Any) -> list[str]:
    if not isinstance(config_payload, dict):
        return []
    plugin_candidates = [
        config_payload.get("plugins"),
        config_payload.get("plugin"),
        config_payload.get("_plugins"),
    ]
    names: set[str] = set()
    for candidate in plugin_candidates:
        if isinstance(candidate, dict):
            for key in candidate.keys():
                if isinstance(key, str):
                    names.add(key)
        elif isinstance(candidate, list):
            for entry in candidate:
                if isinstance(entry, str):
                    names.add(entry)
                elif isinstance(entry, dict):
                    for key in ("name", "plugin", "directory"):
                        value = entry.get(key)
                        if isinstance(value, str):
                            names.add(value)
    return sorted(names)


def extract_plugins_from_itemtypes(itemtypes: list[str]) -> list[str]:
    names: set[str] = set()
    for itemtype in itemtypes:
        if not isinstance(itemtype, str):
            continue
        if not itemtype.lower().startswith("plugin"):
            continue
        # Examples:
        # PluginMyThingItem -> MyThing
        # plugin_mything_items -> mything
        stripped = itemtype[len("plugin") :]
        stripped = stripped.lstrip("_")
        if not stripped:
            continue
        match = re.match(r"([A-Za-z0-9]+)", stripped)
        if match:
            names.add(match.group(1))
    return sorted(names)


def summarize_capabilities(client: Any, openapi: dict[str, Any] | None = None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "mode": getattr(client, "mode", "unknown"),
        "engine": getattr(client, "engine", "unknown"),
        "api_version": getattr(client, "api_version", None),
        "supports_graphql": True,
        "supports_v2": getattr(client, "mode", None) == "v2",
    }

    if isinstance(openapi, dict) and openapi:
        summary["openapi_loaded"] = True
        paths = openapi.get("paths")
        summary["openapi_paths"] = len(paths) if isinstance(paths, dict) else 0
        summary["known_itemtypes"] = infer_itemtypes_from_paths(openapi)
    else:
        summary["openapi_loaded"] = False

    return summary
