"""GraphQL schema helpers."""

from __future__ import annotations

from glpikit.models import GraphQLResponse


def extract_type_names(schema_response: GraphQLResponse) -> list[str]:
    data = schema_response.data or {}
    schema = data.get("__schema") if isinstance(data, dict) else None
    if not isinstance(schema, dict):
        return []
    types = schema.get("types")
    if not isinstance(types, list):
        return []
    names: list[str] = []
    for entry in types:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            names.append(entry["name"])
    return names
