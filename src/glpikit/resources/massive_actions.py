"""Massive actions helpers."""

from __future__ import annotations

from typing import Any

from glpikit.v2 import OpenAPIOperation

from .base import AsyncResourceBase, ResourceBase


def _normalize(text: str) -> str:
    return "".join(ch for ch in text.lower() if ch.isalnum())


def _item_aliases(itemtype: str) -> set[str]:
    normalized = _normalize(itemtype)
    aliases = {normalized}
    if normalized.endswith("s") and len(normalized) > 1:
        aliases.add(normalized[:-1])
    else:
        aliases.add(normalized + "s")
    return aliases


def _is_itemtype_param(name: str) -> bool:
    lowered = name.lower()
    return "itemtype" in lowered or lowered in {"type", "item"}


def _operation_score(operation_id: str, operation: OpenAPIOperation, itemtype: str, *, apply: bool) -> int:
    aliases = _item_aliases(itemtype)
    operation_text = f"{operation_id}/{operation.path}"
    normalized_text = _normalize(operation_text)
    method = operation.method.upper()
    score = 0

    if "massive" in normalized_text or "bulk" in normalized_text:
        score += 10
    else:
        return -1

    if apply and method in {"POST", "PUT", "PATCH"}:
        score += 6
    elif not apply and method == "GET":
        score += 6
    else:
        return -1

    if any(alias in normalized_text for alias in aliases):
        score += 4

    known_itemtype_path_params = [param for param in operation.path_params if _is_itemtype_param(param)]
    known_itemtype_query_params = [param for param in operation.query_params if _is_itemtype_param(param)]
    if known_itemtype_path_params or known_itemtype_query_params:
        score += 3

    unknown_required_path = [param for param in operation.path_params if not _is_itemtype_param(param)]
    if unknown_required_path:
        return -1

    unknown_required_query = [
        param
        for param in operation.required_query_params
        if not _is_itemtype_param(param)
    ]
    if unknown_required_query:
        return -1

    if operation.required_header_params or operation.required_cookie_params:
        return -1

    if apply and operation.has_request_body:
        score += 2

    return score


def _select_v2_operation(v2: Any, itemtype: str, *, apply: bool) -> str | None:
    best_operation: str | None = None
    best_score = -1
    for operation_id, operation in v2._operations.items():
        score = _operation_score(operation_id, operation, itemtype, apply=apply)
        if score > best_score:
            best_score = score
            best_operation = operation_id
    return best_operation


def _kwargs_with_itemtype(v2: Any, operation_id: str, itemtype: str) -> dict[str, Any]:
    operation = v2._operations.get(operation_id)
    if operation is None:
        return {}

    kwargs: dict[str, Any] = {}
    for path_param in operation.path_params:
        if _is_itemtype_param(path_param):
            kwargs[path_param] = itemtype
    for query_param in operation.query_params:
        if _is_itemtype_param(query_param):
            kwargs[query_param] = itemtype
    return kwargs


def _apply_payload_for_operation(operation: OpenAPIOperation, *, action: str, ids: list[int], parameters: dict[str, Any] | None) -> dict[str, Any]:
    payload = {
        "action": action,
        "ids": ids,
        "parameters": parameters or {},
    }
    schema = operation.request_body_schema
    if isinstance(schema, dict):
        properties = schema.get("properties")
        if isinstance(properties, dict) and "input" in properties:
            return {"input": payload}
    return payload


class MassiveActionsNamespace:
    def __init__(self, resource: "MassiveActionsResource", itemtype: str) -> None:
        self.resource = resource
        self.itemtype = itemtype

    def list(self) -> Any:
        return self.resource.list(self.itemtype)

    def apply(
        self,
        action: str,
        ids: list[int],
        parameters: dict[str, Any] | None = None,
        *,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        return self.resource.apply(
            self.itemtype,
            action=action,
            ids=ids,
            parameters=parameters,
            confirmed=confirmed,
            dry_run=dry_run,
        )


class AsyncMassiveActionsNamespace:
    def __init__(self, resource: "AsyncMassiveActionsResource", itemtype: str) -> None:
        self.resource = resource
        self.itemtype = itemtype

    async def list(self) -> Any:
        return await self.resource.list(self.itemtype)

    async def apply(
        self,
        action: str,
        ids: list[int],
        parameters: dict[str, Any] | None = None,
        *,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        return await self.resource.apply(
            self.itemtype,
            action=action,
            ids=ids,
            parameters=parameters,
            confirmed=confirmed,
            dry_run=dry_run,
        )


class MassiveActionsResource(ResourceBase):
    def for_itemtype(self, itemtype: str) -> MassiveActionsNamespace:
        return MassiveActionsNamespace(self, itemtype)

    def list(self, itemtype: str) -> Any:
        if self.client.mode != "v1":
            self.client.v2.load_openapi()
            operation_id = _select_v2_operation(self.client.v2, itemtype, apply=False)
            if operation_id is None:
                raise NotImplementedError("massive actions operation not found for v2")
            kwargs = _kwargs_with_itemtype(self.client.v2, operation_id, itemtype)
            return self.client.v2.call(operation_id, **kwargs)
        path = f"/apirest.php/getMassiveActions/{itemtype}"
        return self._request("GET", path)

    def apply(
        self,
        itemtype: str,
        *,
        action: str,
        ids: list[int],
        parameters: dict[str, Any] | None = None,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        if self.client.mode != "v1":
            self.client.v2.load_openapi()
            operation_id = _select_v2_operation(self.client.v2, itemtype, apply=True)
            if operation_id is None:
                raise NotImplementedError("massive actions operation not found for v2")
            kwargs = _kwargs_with_itemtype(self.client.v2, operation_id, itemtype)
            operation = self.client.v2._operations[operation_id]
            payload = _apply_payload_for_operation(
                operation,
                action=action,
                ids=ids,
                parameters=parameters,
            )
            kwargs["json"] = payload
            return self.client.v2.call(
                operation_id,
                confirmed=confirmed,
                dry_run=dry_run,
                **kwargs,
            )
        path = f"/apirest.php/applyMassiveAction/{itemtype}"
        payload = {
            "input": {
                "action": action,
                "ids": ids,
                "parameters": parameters or {},
            }
        }
        return self._request(
            "POST",
            path,
            json=payload,
            confirmed=confirmed,
            dry_run=dry_run,
        )


class AsyncMassiveActionsResource(AsyncResourceBase):
    def for_itemtype(self, itemtype: str) -> AsyncMassiveActionsNamespace:
        return AsyncMassiveActionsNamespace(self, itemtype)

    async def list(self, itemtype: str) -> Any:
        if self.client.mode != "v1":
            await self.client.v2.load_openapi()
            operation_id = _select_v2_operation(self.client.v2, itemtype, apply=False)
            if operation_id is None:
                raise NotImplementedError("massive actions operation not found for v2")
            kwargs = _kwargs_with_itemtype(self.client.v2, operation_id, itemtype)
            return await self.client.v2.call(operation_id, **kwargs)
        path = f"/apirest.php/getMassiveActions/{itemtype}"
        return await self._request("GET", path)

    async def apply(
        self,
        itemtype: str,
        *,
        action: str,
        ids: list[int],
        parameters: dict[str, Any] | None = None,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        if self.client.mode != "v1":
            await self.client.v2.load_openapi()
            operation_id = _select_v2_operation(self.client.v2, itemtype, apply=True)
            if operation_id is None:
                raise NotImplementedError("massive actions operation not found for v2")
            kwargs = _kwargs_with_itemtype(self.client.v2, operation_id, itemtype)
            operation = self.client.v2._operations[operation_id]
            payload = _apply_payload_for_operation(
                operation,
                action=action,
                ids=ids,
                parameters=parameters,
            )
            kwargs["json"] = payload
            return await self.client.v2.call(
                operation_id,
                confirmed=confirmed,
                dry_run=dry_run,
                **kwargs,
            )
        path = f"/apirest.php/applyMassiveAction/{itemtype}"
        payload = {
            "input": {
                "action": action,
                "ids": ids,
                "parameters": parameters or {},
            }
        }
        return await self._request(
            "POST",
            path,
            json=payload,
            confirmed=confirmed,
            dry_run=dry_run,
        )
