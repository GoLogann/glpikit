"""Generic domain resource wrappers."""

from __future__ import annotations

from typing import Any, Sequence

from .base import AsyncResourceBase, ResourceBase


class GenericItemtypeResource(ResourceBase):
    itemtype: str

    def get(self, item_id: int, *, params: dict[str, Any] | None = None) -> Any:
        return self.client.items.get(self.itemtype, item_id, params=params)

    def list(self, *, params: dict[str, Any] | None = None) -> Sequence[Any]:
        return self.client.items.list(self.itemtype, params=params)

    def create(self, payload: dict[str, Any]) -> Any:
        return self.client.items.create(self.itemtype, payload)

    def update(self, item_id: int, payload: dict[str, Any]) -> Any:
        return self.client.items.update(self.itemtype, item_id, payload)

    def delete(self, item_id: int, *, force_purge: bool = False) -> Any:
        return self.client.items.delete(self.itemtype, item_id, force_purge=force_purge)


class AsyncGenericItemtypeResource(AsyncResourceBase):
    itemtype: str

    async def get(self, item_id: int, *, params: dict[str, Any] | None = None) -> Any:
        return await self.client.items.get(self.itemtype, item_id, params=params)

    async def list(self, *, params: dict[str, Any] | None = None) -> Sequence[Any]:
        return await self.client.items.list(self.itemtype, params=params)

    async def create(self, payload: dict[str, Any]) -> Any:
        return await self.client.items.create(self.itemtype, payload)

    async def update(self, item_id: int, payload: dict[str, Any]) -> Any:
        return await self.client.items.update(self.itemtype, item_id, payload)

    async def delete(self, item_id: int, *, force_purge: bool = False) -> Any:
        return await self.client.items.delete(self.itemtype, item_id, force_purge=force_purge)
