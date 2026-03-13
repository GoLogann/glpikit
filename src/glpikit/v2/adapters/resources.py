"""Adapters to map itemtypes to likely v2 operation ids."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from glpikit.v2.resources import AsyncV2Resources, V2Resources


def _normalize(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def _item_aliases(itemtype: str) -> set[str]:
    normalized = _normalize(itemtype)
    aliases = {normalized}
    if normalized.endswith("ies"):
        aliases.add(normalized[:-3] + "y")
    if normalized.endswith("s") and len(normalized) > 1:
        aliases.add(normalized[:-1])
    else:
        aliases.add(normalized + "s")
    return aliases


def _match_action(operation_id: str) -> str | None:
    normalized = _normalize(operation_id)
    if normalized.startswith(("get", "read", "show")):
        return "get"
    if normalized.startswith(("list", "search", "find", "browse")):
        return "list"
    if normalized.startswith(("create", "add", "new", "post")):
        return "create"
    if normalized.startswith(("update", "edit", "put", "patch")):
        return "update"
    if normalized.startswith(("delete", "remove")):
        return "delete"
    return None


def _build_action_map(operations: list[str], itemtype: str) -> dict[str, str]:
    aliases = _item_aliases(itemtype)
    mapping: dict[str, str] = {}
    for operation_id in operations:
        normalized = _normalize(operation_id)
        if not any(alias in normalized for alias in aliases):
            continue
        action = _match_action(operation_id)
        if action and action not in mapping:
            mapping[action] = operation_id
    return mapping


@dataclass(slots=True)
class V2ResourceAdapter:
    resources: V2Resources
    itemtype: str

    def _actions(self) -> dict[str, str]:
        return _build_action_map(self.resources.operations(), self.itemtype)

    def operations(self) -> dict[str, str]:
        return dict(self._actions())

    def has(self, action: str) -> bool:
        return action in self._actions()

    def _operation_for(self, action: str) -> str:
        mapping = self._actions()
        operation_id = mapping.get(action)
        if operation_id is None:
            raise KeyError(f"No '{action}' operation found for itemtype '{self.itemtype}'")
        return operation_id

    def list(self, **kwargs: Any) -> Any:
        return self.resources.call(self._operation_for("list"), **kwargs)

    def get(self, **kwargs: Any) -> Any:
        return self.resources.call(self._operation_for("get"), **kwargs)

    def create(self, *, json: Any = None, **kwargs: Any) -> Any:
        return self.resources.call(self._operation_for("create"), json=json, **kwargs)

    def update(self, *, json: Any = None, **kwargs: Any) -> Any:
        return self.resources.call(self._operation_for("update"), json=json, **kwargs)

    def delete(self, **kwargs: Any) -> Any:
        return self.resources.call(self._operation_for("delete"), **kwargs)


@dataclass(slots=True)
class AsyncV2ResourceAdapter:
    resources: AsyncV2Resources
    itemtype: str

    async def _actions(self) -> dict[str, str]:
        return _build_action_map(await self.resources.operations(), self.itemtype)

    async def operations(self) -> dict[str, str]:
        return dict(await self._actions())

    async def has(self, action: str) -> bool:
        return action in await self._actions()

    async def _operation_for(self, action: str) -> str:
        mapping = await self._actions()
        operation_id = mapping.get(action)
        if operation_id is None:
            raise KeyError(f"No '{action}' operation found for itemtype '{self.itemtype}'")
        return operation_id

    async def list(self, **kwargs: Any) -> Any:
        return await self.resources.call(await self._operation_for("list"), **kwargs)

    async def get(self, **kwargs: Any) -> Any:
        return await self.resources.call(await self._operation_for("get"), **kwargs)

    async def create(self, *, json: Any = None, **kwargs: Any) -> Any:
        return await self.resources.call(await self._operation_for("create"), json=json, **kwargs)

    async def update(self, *, json: Any = None, **kwargs: Any) -> Any:
        return await self.resources.call(await self._operation_for("update"), json=json, **kwargs)

    async def delete(self, **kwargs: Any) -> Any:
        return await self.resources.call(await self._operation_for("delete"), **kwargs)
