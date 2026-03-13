"""Runtime typing from OpenAPI schemas for v2 operations."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, create_model


def _resolve_ref(openapi: dict[str, Any], ref: str) -> dict[str, Any] | None:
    if not ref.startswith("#/components/schemas/"):
        return None
    name = ref.split("/")[-1]
    components = openapi.get("components")
    if not isinstance(components, dict):
        return None
    schemas = components.get("schemas")
    if not isinstance(schemas, dict):
        return None
    schema = schemas.get(name)
    return schema if isinstance(schema, dict) else None


def _python_type_from_schema(
    openapi: dict[str, Any],
    schema: dict[str, Any],
    cache: dict[str, type[Any]],
    *,
    model_name: str,
) -> Any:
    if not isinstance(schema, dict):
        return Any

    all_of = schema.get("allOf")
    if isinstance(all_of, list):
        merged = _merge_all_of(openapi, all_of)
        if merged:
            return _python_type_from_schema(openapi, merged, cache, model_name=model_name)

    one_of = schema.get("oneOf")
    if isinstance(one_of, list) and one_of:
        options = [
            _python_type_from_schema(
                openapi,
                option if isinstance(option, dict) else {},
                cache,
                model_name=f"{model_name}Option{index}",
            )
            for index, option in enumerate(one_of)
        ]
        return _build_union(options)

    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and any_of:
        options = [
            _python_type_from_schema(
                openapi,
                option if isinstance(option, dict) else {},
                cache,
                model_name=f"{model_name}Any{index}",
            )
            for index, option in enumerate(any_of)
        ]
        return _build_union(options)

    ref = schema.get("$ref")
    if isinstance(ref, str):
        resolved = _resolve_ref(openapi, ref)
        if resolved is None:
            return Any
        ref_name = ref.split("/")[-1]
        if ref_name in cache:
            return cache[ref_name]
        return _python_type_from_schema(openapi, resolved, cache, model_name=ref_name)

    schema_type = schema.get("type")
    if schema_type == "string":
        return str
    if schema_type == "integer":
        return int
    if schema_type == "number":
        return float
    if schema_type == "boolean":
        return bool

    if schema_type == "array":
        items = schema.get("items")
        if isinstance(items, dict):
            inner = _python_type_from_schema(openapi, items, cache, model_name=f"{model_name}Item")
        else:
            inner = Any
        root_name = f"{model_name}List"
        if root_name in cache:
            return cache[root_name]
        model = type(root_name, (RootModel[list[inner]],), {})
        cache[root_name] = model
        return model

    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return dict[str, Any]
        required = schema.get("required")
        required_fields = set(required) if isinstance(required, list) else set()

        fields: dict[str, tuple[Any, Any]] = {}
        for key, prop_schema in properties.items():
            if not isinstance(key, str) or not isinstance(prop_schema, dict):
                continue
            annotation = _python_type_from_schema(
                openapi,
                prop_schema,
                cache,
                model_name=f"{model_name}_{key.title()}",
            )
            default = ... if key in required_fields else None
            fields[key] = (annotation, default)

        current_name = model_name if model_name not in cache else f"{model_name}Model"
        if current_name in cache:
            return cache[current_name]
        model = create_model(current_name, __base__=BaseModel, **fields)
        cache[current_name] = model
        base_type: Any = model
        if schema.get("nullable") is True:
            return base_type | None
        return base_type

    base_type: Any = Any
    if schema.get("nullable") is True:
        return base_type | None
    return base_type


def _merge_all_of(openapi: dict[str, Any], schemas: list[Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
    for candidate in schemas:
        if not isinstance(candidate, dict):
            continue
        source = candidate
        ref = source.get("$ref")
        if isinstance(ref, str):
            resolved = _resolve_ref(openapi, ref)
            if isinstance(resolved, dict):
                source = resolved

        properties = source.get("properties")
        if isinstance(properties, dict):
            merged["properties"].update(properties)

        required = source.get("required")
        if isinstance(required, list):
            merged["required"].extend(value for value in required if isinstance(value, str))

    # Deduplicate required fields preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for value in merged["required"]:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    merged["required"] = deduped
    return merged


def _build_union(options: list[Any]) -> Any:
    filtered = [option for option in options if option is not Any]
    if not filtered:
        return Any
    current = filtered[0]
    for option in filtered[1:]:
        current = current | option
    return current


def _safe_field_name(name: str) -> str:
    sanitized = re.sub(r"[^0-9a-zA-Z_]", "_", name).strip("_")
    if not sanitized:
        sanitized = "field"
    if sanitized[0].isdigit():
        sanitized = f"f_{sanitized}"
    return sanitized


def build_operation_response_models(openapi: dict[str, Any]) -> dict[str, type[Any] | Any]:
    models: dict[str, type[Any] | Any] = {}
    cache: dict[str, type[Any]] = {}
    paths = openapi.get("paths")
    if not isinstance(paths, dict):
        return models

    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str):
                continue

            responses = operation.get("responses")
            if not isinstance(responses, dict):
                continue

            response_schema: dict[str, Any] | None = None
            for status_code, response in responses.items():
                if not str(status_code).startswith("2"):
                    continue
                if not isinstance(response, dict):
                    continue
                content = response.get("content")
                if not isinstance(content, dict):
                    continue
                json_content = content.get("application/json")
                if not isinstance(json_content, dict):
                    continue
                schema = json_content.get("schema")
                if isinstance(schema, dict):
                    response_schema = schema
                    break

            if response_schema is None:
                continue

            model = _python_type_from_schema(
                openapi,
                response_schema,
                cache,
                model_name=f"{operation_id.title()}Response",
            )
            models[operation_id] = model

    return models


def build_operation_request_models(openapi: dict[str, Any]) -> dict[str, type[BaseModel]]:
    models: dict[str, type[BaseModel]] = {}
    type_cache: dict[str, type[Any]] = {}

    class _OperationRequest(BaseModel):
        model_config = ConfigDict(populate_by_name=True, extra="forbid")

    paths = openapi.get("paths")
    if not isinstance(paths, dict):
        return models

    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        path_level_params = path_item.get("parameters")
        path_params: list[dict[str, Any]] = []
        if isinstance(path_level_params, list):
            path_params = [entry for entry in path_level_params if isinstance(entry, dict)]

        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            if not isinstance(operation, dict):
                continue

            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str):
                continue

            parameters = list(path_params)
            operation_params = operation.get("parameters")
            if isinstance(operation_params, list):
                parameters.extend([entry for entry in operation_params if isinstance(entry, dict)])

            fields: dict[str, tuple[Any, Any]] = {}
            names_seen: set[str] = set()
            for parameter in parameters:
                original_name = parameter.get("name")
                if not isinstance(original_name, str):
                    continue
                required = bool(parameter.get("required"))
                schema = parameter.get("schema") if isinstance(parameter.get("schema"), dict) else {}
                annotation = _python_type_from_schema(
                    openapi,
                    schema if isinstance(schema, dict) else {},
                    type_cache,
                    model_name=f"{operation_id.title()}Param{_safe_field_name(original_name).title()}",
                )

                field_name = _safe_field_name(original_name)
                suffix = 1
                while field_name in names_seen:
                    suffix += 1
                    field_name = f"{_safe_field_name(original_name)}_{suffix}"
                names_seen.add(field_name)

                default: Any = ... if required else None
                if field_name != original_name:
                    fields[field_name] = (annotation, Field(default=default, alias=original_name))
                else:
                    fields[field_name] = (annotation, default)

            request_body = operation.get("requestBody")
            if isinstance(request_body, dict):
                content = request_body.get("content")
                if isinstance(content, dict):
                    preferred = content.get("application/json")
                    schema: dict[str, Any] | None = None
                    if isinstance(preferred, dict) and isinstance(preferred.get("schema"), dict):
                        schema = preferred["schema"]
                    elif content:
                        first = next(iter(content.values()))
                        if isinstance(first, dict) and isinstance(first.get("schema"), dict):
                            schema = first["schema"]
                    if isinstance(schema, dict):
                        body_type = _python_type_from_schema(
                            openapi,
                            schema,
                            type_cache,
                            model_name=f"{operation_id.title()}RequestBody",
                        )
                        required = bool(request_body.get("required"))
                        fields["json_payload"] = (
                            body_type,
                            Field(default=... if required else None, alias="json"),
                        )
                        fields["body"] = (body_type | None, None)

            if not fields:
                continue

            model = create_model(
                f"{operation_id.title()}Request",
                __base__=_OperationRequest,
                **fields,
            )
            models[operation_id] = model

    return models


def parse_typed_response(model: type[Any] | Any, payload: Any) -> Any:
    if isinstance(model, type) and issubclass(model, BaseModel):
        return model.model_validate(payload)
    return payload
