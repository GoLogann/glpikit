"""Spec-driven and dynamic accessors for REST v2 resources."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .discovery import discover_openapi, discover_openapi_async
from .openapi import OpenAPIOperation, build_operation_index
from .typed import (
    build_operation_request_models,
    build_operation_response_models,
    parse_typed_response,
)

if TYPE_CHECKING:
    from glpikit.async_client import AsyncGLPI
    from glpikit.client import GLPI
    from glpikit.v2.adapters import AsyncV2ResourceAdapter, V2ResourceAdapter
    from glpikit.v2.generated import AsyncV2GeneratedClient, V2GeneratedClient


def _coerce_scalar(value: Any, schema_type: str) -> Any:
    if schema_type == "integer":
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(value)
        if isinstance(value, str):
            return int(value.strip())
    if schema_type == "number":
        if isinstance(value, bool):
            return float(int(value))
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            return float(value.strip())
    if schema_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off"}:
                return False
    return value


def _coerce_from_schema(value: Any, schema: dict[str, Any] | None) -> Any:
    if not isinstance(schema, dict):
        return value

    if value is None:
        return None

    schema_type = schema.get("type")
    if not isinstance(schema_type, str):
        return value

    try:
        if schema_type in {"integer", "number", "boolean"}:
            return _coerce_scalar(value, schema_type)

        if schema_type == "array":
            if isinstance(value, str):
                raw = value.strip()
                if raw.startswith("["):
                    decoded = json.loads(raw)
                    return decoded if isinstance(decoded, list) else [decoded]
                if not raw:
                    return []
                return [item.strip() for item in raw.split(",")]
            if isinstance(value, (tuple, set)):
                return list(value)
            return value

        if schema_type == "object":
            if isinstance(value, str):
                raw = value.strip()
                if raw.startswith("{"):
                    decoded = json.loads(raw)
                    if isinstance(decoded, dict):
                        return decoded
                return value
            return value
    except Exception:
        return value

    return value


class V2Resources:
    def __init__(self, client: GLPI) -> None:
        from glpikit.v2.generated import V2GeneratedClient

        self.client = client
        self._openapi: dict[str, Any] | None = None
        self._operations: dict[str, OpenAPIOperation] = {}
        self._request_models: dict[str, type[Any]] = {}
        self._response_models: dict[str, type[Any] | Any] = {}
        self.generated: V2GeneratedClient = V2GeneratedClient(self)

    def _normalize_path(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if path.startswith("/api.php"):
            return path
        if path.startswith("/"):
            return f"/api.php/{self.client.api_version}{path}"
        return f"/api.php/{self.client.api_version}/{path}"

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self.client.raw.request(method, self._normalize_path(path), **kwargs)

    def get(self, resource: str, resource_id: int | None = None, **kwargs: Any) -> Any:
        path = resource if resource_id is None else f"{resource}/{resource_id}"
        return self.request("GET", path, **kwargs)

    def post(self, resource: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> Any:
        return self.request("POST", resource, json=json, data=data, **kwargs)

    def put(self, resource: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> Any:
        return self.request("PUT", resource, json=json, data=data, **kwargs)

    def delete(self, resource: str, *, json: Any = None, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return self.request("DELETE", resource, json=json, params=params, **kwargs)

    def load_openapi(self, *, force_refresh: bool = False) -> dict[str, Any]:
        if self._openapi is not None and not force_refresh:
            return self._openapi
        self._openapi = discover_openapi(self.client, api_version=self.client.api_version)
        self._operations = build_operation_index(self._openapi)
        self._request_models = build_operation_request_models(self._openapi)
        self._response_models = build_operation_response_models(self._openapi)
        return self._openapi

    def operations(self) -> list[str]:
        self.load_openapi()
        return sorted(self._operations.keys())

    def adapter(self, itemtype: str) -> V2ResourceAdapter:
        from glpikit.v2.adapters import V2ResourceAdapter

        return V2ResourceAdapter(self, itemtype)

    def request_model(self, operation_id: str) -> type[Any] | None:
        self.load_openapi()
        return self._request_models.get(operation_id)

    def validate_kwargs(self, operation_id: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        model = self.request_model(operation_id)
        if model is None:
            return dict(kwargs)

        payload = dict(kwargs)
        if "body" in payload and "json" not in payload:
            payload["json"] = payload["body"]

        validated = model.model_validate(payload)
        data = validated.model_dump(exclude_none=True, by_alias=True)
        if "body" in data and "json" not in data:
            data["json"] = data["body"]
        return data

    def call(
        self,
        operation_id: str,
        *,
        confirmed: bool = False,
        dry_run: bool | None = None,
        validate_request: bool = False,
        **kwargs: Any,
    ) -> Any:
        self.load_openapi()
        if validate_request:
            kwargs = self.validate_kwargs(operation_id, kwargs)
        operation = self._operations.get(operation_id)
        if operation is None:
            raise KeyError(f"Unknown operation_id: {operation_id}")

        path = operation.path
        consumed: set[str] = set()
        for parameter in operation.path_params:
            if parameter not in kwargs:
                raise ValueError(f"Missing path parameter: {parameter}")
            value = _coerce_from_schema(
                kwargs[parameter],
                operation.parameter_schemas.get(parameter),
            )
            consumed.add(parameter)
            path = path.replace(f"{{{parameter}}}", str(value))

        query: dict[str, Any] = {}
        headers: dict[str, str] = {}
        cookies: dict[str, str] = {}
        for parameter in operation.query_params:
            if parameter in kwargs:
                query[parameter] = _coerce_from_schema(
                    kwargs[parameter],
                    operation.parameter_schemas.get(parameter),
                )
                consumed.add(parameter)

        for parameter in operation.header_params:
            if parameter in kwargs:
                coerced = _coerce_from_schema(
                    kwargs[parameter],
                    operation.parameter_schemas.get(parameter),
                )
                headers[parameter] = str(coerced)
                consumed.add(parameter)

        for parameter in operation.cookie_params:
            if parameter in kwargs:
                coerced = _coerce_from_schema(
                    kwargs[parameter],
                    operation.parameter_schemas.get(parameter),
                )
                cookies[parameter] = str(coerced)
                consumed.add(parameter)

        for required_name in operation.required_query_params:
            if required_name not in query:
                raise ValueError(f"Missing required query parameter: {required_name}")
        for required_name in operation.required_header_params:
            if required_name not in headers:
                raise ValueError(f"Missing required header parameter: {required_name}")
        for required_name in operation.required_cookie_params:
            if required_name not in cookies:
                raise ValueError(f"Missing required cookie parameter: {required_name}")

        json_payload = kwargs.get("json")
        if "json" in kwargs:
            consumed.add("json")

        body_payload = kwargs.get("body")
        if "body" in kwargs:
            consumed.add("body")

        if json_payload is None and operation.has_request_body:
            json_payload = body_payload
        json_payload = _coerce_from_schema(json_payload, operation.request_body_schema)
        if operation.request_body_required and json_payload is None:
            raise ValueError("Missing required request body")

        extra_params = {
            key: value
            for key, value in kwargs.items()
            if key not in consumed and key not in {"params", "headers", "data", "files", "cookies"}
        }
        if extra_params:
            query.update(extra_params)

        explicit_params = kwargs.get("params")
        if isinstance(explicit_params, dict):
            query.update(explicit_params)

        explicit_headers = kwargs.get("headers")
        if isinstance(explicit_headers, dict):
            headers.update({str(k): str(v) for k, v in explicit_headers.items()})

        explicit_cookies = kwargs.get("cookies")
        if isinstance(explicit_cookies, dict):
            cookies.update({str(k): str(v) for k, v in explicit_cookies.items()})

        request_headers = headers or None
        if cookies:
            cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
            request_headers = request_headers or {}
            request_headers["Cookie"] = cookie_header

        return self.request(
            operation.method,
            path,
            params=query or None,
            json=json_payload,
            data=kwargs.get("data"),
            files=kwargs.get("files"),
            headers=request_headers,
            confirmed=confirmed,
            dry_run=dry_run,
        )

    def call_typed(
        self,
        operation_id: str,
        *,
        confirmed: bool = False,
        dry_run: bool | None = None,
        validate_request: bool = False,
        **kwargs: Any,
    ) -> Any:
        payload = self.call(
            operation_id,
            confirmed=confirmed,
            dry_run=dry_run,
            validate_request=validate_request,
            **kwargs,
        )
        model = self._response_models.get(operation_id)
        if model is None:
            return payload
        return parse_typed_response(model, payload)


class AsyncV2Resources:
    def __init__(self, client: AsyncGLPI) -> None:
        from glpikit.v2.generated import AsyncV2GeneratedClient

        self.client = client
        self._openapi: dict[str, Any] | None = None
        self._operations: dict[str, OpenAPIOperation] = {}
        self._request_models: dict[str, type[Any]] = {}
        self._response_models: dict[str, type[Any] | Any] = {}
        self.generated: AsyncV2GeneratedClient = AsyncV2GeneratedClient(self)

    def _normalize_path(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if path.startswith("/api.php"):
            return path
        if path.startswith("/"):
            return f"/api.php/{self.client.api_version}{path}"
        return f"/api.php/{self.client.api_version}/{path}"

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        return await self.client.raw.request(method, self._normalize_path(path), **kwargs)

    async def get(self, resource: str, resource_id: int | None = None, **kwargs: Any) -> Any:
        path = resource if resource_id is None else f"{resource}/{resource_id}"
        return await self.request("GET", path, **kwargs)

    async def post(self, resource: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> Any:
        return await self.request("POST", resource, json=json, data=data, **kwargs)

    async def put(self, resource: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> Any:
        return await self.request("PUT", resource, json=json, data=data, **kwargs)

    async def delete(
        self,
        resource: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        return await self.request("DELETE", resource, json=json, params=params, **kwargs)

    async def load_openapi(self, *, force_refresh: bool = False) -> dict[str, Any]:
        if self._openapi is not None and not force_refresh:
            return self._openapi
        self._openapi = await discover_openapi_async(self.client, api_version=self.client.api_version)
        self._operations = build_operation_index(self._openapi)
        self._request_models = build_operation_request_models(self._openapi)
        self._response_models = build_operation_response_models(self._openapi)
        return self._openapi

    async def operations(self) -> list[str]:
        await self.load_openapi()
        return sorted(self._operations.keys())

    def adapter(self, itemtype: str) -> AsyncV2ResourceAdapter:
        from glpikit.v2.adapters import AsyncV2ResourceAdapter

        return AsyncV2ResourceAdapter(self, itemtype)

    async def request_model(self, operation_id: str) -> type[Any] | None:
        await self.load_openapi()
        return self._request_models.get(operation_id)

    async def validate_kwargs(self, operation_id: str, kwargs: dict[str, Any]) -> dict[str, Any]:
        model = await self.request_model(operation_id)
        if model is None:
            return dict(kwargs)

        payload = dict(kwargs)
        if "body" in payload and "json" not in payload:
            payload["json"] = payload["body"]

        validated = model.model_validate(payload)
        data = validated.model_dump(exclude_none=True, by_alias=True)
        if "body" in data and "json" not in data:
            data["json"] = data["body"]
        return data

    async def call(
        self,
        operation_id: str,
        *,
        confirmed: bool = False,
        dry_run: bool | None = None,
        validate_request: bool = False,
        **kwargs: Any,
    ) -> Any:
        await self.load_openapi()
        if validate_request:
            kwargs = await self.validate_kwargs(operation_id, kwargs)
        operation = self._operations.get(operation_id)
        if operation is None:
            raise KeyError(f"Unknown operation_id: {operation_id}")

        path = operation.path
        consumed: set[str] = set()
        for parameter in operation.path_params:
            if parameter not in kwargs:
                raise ValueError(f"Missing path parameter: {parameter}")
            value = _coerce_from_schema(
                kwargs[parameter],
                operation.parameter_schemas.get(parameter),
            )
            consumed.add(parameter)
            path = path.replace(f"{{{parameter}}}", str(value))

        query: dict[str, Any] = {}
        headers: dict[str, str] = {}
        cookies: dict[str, str] = {}
        for parameter in operation.query_params:
            if parameter in kwargs:
                query[parameter] = _coerce_from_schema(
                    kwargs[parameter],
                    operation.parameter_schemas.get(parameter),
                )
                consumed.add(parameter)

        for parameter in operation.header_params:
            if parameter in kwargs:
                coerced = _coerce_from_schema(
                    kwargs[parameter],
                    operation.parameter_schemas.get(parameter),
                )
                headers[parameter] = str(coerced)
                consumed.add(parameter)

        for parameter in operation.cookie_params:
            if parameter in kwargs:
                coerced = _coerce_from_schema(
                    kwargs[parameter],
                    operation.parameter_schemas.get(parameter),
                )
                cookies[parameter] = str(coerced)
                consumed.add(parameter)

        for required_name in operation.required_query_params:
            if required_name not in query:
                raise ValueError(f"Missing required query parameter: {required_name}")
        for required_name in operation.required_header_params:
            if required_name not in headers:
                raise ValueError(f"Missing required header parameter: {required_name}")
        for required_name in operation.required_cookie_params:
            if required_name not in cookies:
                raise ValueError(f"Missing required cookie parameter: {required_name}")

        json_payload = kwargs.get("json")
        if "json" in kwargs:
            consumed.add("json")

        body_payload = kwargs.get("body")
        if "body" in kwargs:
            consumed.add("body")

        if json_payload is None and operation.has_request_body:
            json_payload = body_payload
        json_payload = _coerce_from_schema(json_payload, operation.request_body_schema)
        if operation.request_body_required and json_payload is None:
            raise ValueError("Missing required request body")

        extra_params = {
            key: value
            for key, value in kwargs.items()
            if key not in consumed and key not in {"params", "headers", "data", "files", "cookies"}
        }
        if extra_params:
            query.update(extra_params)

        explicit_params = kwargs.get("params")
        if isinstance(explicit_params, dict):
            query.update(explicit_params)

        explicit_headers = kwargs.get("headers")
        if isinstance(explicit_headers, dict):
            headers.update({str(k): str(v) for k, v in explicit_headers.items()})

        explicit_cookies = kwargs.get("cookies")
        if isinstance(explicit_cookies, dict):
            cookies.update({str(k): str(v) for k, v in explicit_cookies.items()})

        request_headers = headers or None
        if cookies:
            cookie_header = "; ".join(f"{key}={value}" for key, value in cookies.items())
            request_headers = request_headers or {}
            request_headers["Cookie"] = cookie_header

        return await self.request(
            operation.method,
            path,
            params=query or None,
            json=json_payload,
            data=kwargs.get("data"),
            files=kwargs.get("files"),
            headers=request_headers,
            confirmed=confirmed,
            dry_run=dry_run,
        )

    async def call_typed(
        self,
        operation_id: str,
        *,
        confirmed: bool = False,
        dry_run: bool | None = None,
        validate_request: bool = False,
        **kwargs: Any,
    ) -> Any:
        payload = await self.call(
            operation_id,
            confirmed=confirmed,
            dry_run=dry_run,
            validate_request=validate_request,
            **kwargs,
        )
        model = self._response_models.get(operation_id)
        if model is None:
            return payload
        return parse_typed_response(model, payload)
