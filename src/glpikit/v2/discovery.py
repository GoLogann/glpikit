"""v2 API discovery helpers."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from glpikit.async_client import AsyncGLPI
    from glpikit.client import GLPI


def _candidate_paths(api_version: str) -> list[str]:
    return [
        "/api.php/doc/openapi.json",
        "/api.php/doc?format=openapi",
        f"/api.php/{api_version}/doc/openapi.json",
        "/api.php/doc",
    ]


def discover_openapi(client: GLPI, api_version: str = "v2") -> dict[str, Any]:
    for path in _candidate_paths(api_version):
        try:
            payload = client.raw.get(path)
            if isinstance(payload, dict):
                if payload:
                    return payload
                continue
            if isinstance(payload, str):
                try:
                    decoded = json.loads(payload)
                except ValueError:
                    continue
                if isinstance(decoded, dict) and decoded:
                    return decoded
        except Exception:
            continue
    return {}


async def discover_openapi_async(
    client: AsyncGLPI, api_version: str = "v2"
) -> dict[str, Any]:
    for path in _candidate_paths(api_version):
        try:
            payload = await client.raw.get(path)
            if isinstance(payload, dict):
                if payload:
                    return payload
                continue
            if isinstance(payload, str):
                try:
                    decoded = json.loads(payload)
                except ValueError:
                    continue
                if isinstance(decoded, dict) and decoded:
                    return decoded
        except Exception:
            continue
    return {}
