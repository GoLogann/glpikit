"""Helpers to index GLPI OpenAPI documents."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class OpenAPIOperation:
    operation_id: str
    method: str
    path: str
    path_params: list[str]
    query_params: list[str]
    header_params: list[str]
    cookie_params: list[str]
    has_request_body: bool
    required_query_params: list[str]
    required_header_params: list[str]
    required_cookie_params: list[str]
    parameter_schemas: dict[str, dict[str, Any]]
    request_body_required: bool
    request_content_types: list[str]
    request_body_schema: dict[str, Any] | None


def build_operation_index(openapi: dict[str, Any]) -> dict[str, OpenAPIOperation]:
    index: dict[str, OpenAPIOperation] = {}
    paths = openapi.get("paths")
    if not isinstance(paths, dict):
        return index

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_level_params: list[dict[str, Any]] = []
        raw_path_params = path_item.get("parameters")
        if isinstance(raw_path_params, list):
            path_level_params = [p for p in raw_path_params if isinstance(p, dict)]

        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id.strip():
                continue

            parameters: list[dict[str, Any]] = []
            parameters.extend(path_level_params)
            raw_parameters = operation.get("parameters")
            if isinstance(raw_parameters, list):
                parameters.extend([p for p in raw_parameters if isinstance(p, dict)])

            path_params: list[str] = []
            query_params: list[str] = []
            header_params: list[str] = []
            cookie_params: list[str] = []
            required_query_params: list[str] = []
            required_header_params: list[str] = []
            required_cookie_params: list[str] = []
            parameter_schemas: dict[str, dict[str, Any]] = {}
            for parameter in parameters:
                name = parameter.get("name")
                location = parameter.get("in")
                if not isinstance(name, str) or not isinstance(location, str):
                    continue
                schema = parameter.get("schema")
                if isinstance(schema, dict):
                    parameter_schemas[name] = schema
                required = bool(parameter.get("required"))
                if location == "path":
                    path_params.append(name)
                elif location == "query":
                    query_params.append(name)
                    if required:
                        required_query_params.append(name)
                elif location == "header":
                    header_params.append(name)
                    if required:
                        required_header_params.append(name)
                elif location == "cookie":
                    cookie_params.append(name)
                    if required:
                        required_cookie_params.append(name)

            request_body = operation.get("requestBody")
            has_request_body = isinstance(request_body, dict)
            request_body_required = bool(request_body.get("required")) if has_request_body else False
            request_content_types: list[str] = []
            request_body_schema: dict[str, Any] | None = None
            if has_request_body:
                content = request_body.get("content")
                if isinstance(content, dict):
                    request_content_types = [key for key in content if isinstance(key, str)]
                    preferred = content.get("application/json")
                    if isinstance(preferred, dict) and isinstance(preferred.get("schema"), dict):
                        request_body_schema = preferred["schema"]
                    elif request_content_types:
                        fallback = content.get(request_content_types[0])
                        if isinstance(fallback, dict) and isinstance(fallback.get("schema"), dict):
                            request_body_schema = fallback["schema"]

            # Preserve order but remove duplicates (path level + operation level may overlap).
            path_params = list(dict.fromkeys(path_params))
            query_params = list(dict.fromkeys(query_params))
            header_params = list(dict.fromkeys(header_params))
            cookie_params = list(dict.fromkeys(cookie_params))
            required_query_params = list(dict.fromkeys(required_query_params))
            required_header_params = list(dict.fromkeys(required_header_params))
            required_cookie_params = list(dict.fromkeys(required_cookie_params))

            index[operation_id] = OpenAPIOperation(
                operation_id=operation_id,
                method=method.upper(),
                path=path,
                path_params=path_params,
                query_params=query_params,
                header_params=header_params,
                cookie_params=cookie_params,
                has_request_body=has_request_body,
                required_query_params=required_query_params,
                required_header_params=required_header_params,
                required_cookie_params=required_cookie_params,
                parameter_schemas=parameter_schemas,
                request_body_required=request_body_required,
                request_content_types=request_content_types,
                request_body_schema=request_body_schema,
            )

    return index


def infer_itemtypes_from_paths(openapi: dict[str, Any]) -> list[str]:
    paths = openapi.get("paths")
    if not isinstance(paths, dict):
        return []

    itemtypes: set[str] = set()
    for path in paths:
        if not isinstance(path, str):
            continue
        clean = path.strip("/")
        if not clean:
            continue
        parts = [part for part in clean.split("/") if part and not part.startswith("{")]
        if not parts:
            continue

        # Prefer the last non-placeholder segment for resource-like paths.
        candidate = parts[-1]
        if candidate.startswith("v") and len(parts) >= 2:
            candidate = parts[-2]
        if candidate:
            itemtypes.add(candidate)

    return sorted(itemtypes)
