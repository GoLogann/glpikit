"""Plugin-aware generic itemtype access."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import AsyncResourceBase, ResourceBase

if TYPE_CHECKING:
    from glpikit.async_client import AsyncGLPI
    from glpikit.client import GLPI


class PluginItemsResource(ResourceBase):
    def __init__(self, client: GLPI, itemtype: str) -> None:
        super().__init__(client)
        self.itemtype = itemtype

    def get(self, item_id: int, *, params: dict[str, Any] | None = None) -> Any:
        return self.client.items.get(self.itemtype, item_id, params=params)

    def list(self, *, params: dict[str, Any] | None = None) -> Any:
        return self.client.items.list(self.itemtype, params=params)

    def create(self, payload: dict[str, Any]) -> Any:
        return self.client.items.create(self.itemtype, payload)

    def update(self, item_id: int, payload: dict[str, Any]) -> Any:
        return self.client.items.update(self.itemtype, item_id, payload)

    def delete(self, item_id: int, *, force_purge: bool = False) -> Any:
        return self.client.items.delete(self.itemtype, item_id, force_purge=force_purge)


class AsyncPluginItemsResource(AsyncResourceBase):
    def __init__(self, client: AsyncGLPI, itemtype: str) -> None:
        super().__init__(client)
        self.itemtype = itemtype

    async def get(self, item_id: int, *, params: dict[str, Any] | None = None) -> Any:
        return await self.client.items.get(self.itemtype, item_id, params=params)

    async def list(self, *, params: dict[str, Any] | None = None) -> Any:
        return await self.client.items.list(self.itemtype, params=params)

    async def create(self, payload: dict[str, Any]) -> Any:
        return await self.client.items.create(self.itemtype, payload)

    async def update(self, item_id: int, payload: dict[str, Any]) -> Any:
        return await self.client.items.update(self.itemtype, item_id, payload)

    async def delete(self, item_id: int, *, force_purge: bool = False) -> Any:
        return await self.client.items.delete(self.itemtype, item_id, force_purge=force_purge)
