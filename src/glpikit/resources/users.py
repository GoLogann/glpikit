"""User domain resource."""

from __future__ import annotations

from typing import Any

from glpikit.models import User

from .base import AsyncResourceBase, ResourceBase


class UsersResource(ResourceBase):
    def get(self, user_id: int, *, params: dict[str, Any] | None = None) -> User:
        payload = self.client.items.get("User", user_id, params=params)
        return User.model_validate(payload)

    def list(self, *, params: dict[str, Any] | None = None) -> list[User]:
        payload = self.client.items.list("User", params=params)
        return [User.model_validate(entry) for entry in payload]

    def search(self, **kwargs: Any) -> Any:
        return self.client.items.search("User", **kwargs)

    def picture(self, user_id: int) -> bytes:
        path = self.client._user_picture_path(user_id)
        data = self.client._request("GET", path, headers={"Accept": "application/octet-stream"})
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        return bytes(str(data), "utf-8")


class AsyncUsersResource(AsyncResourceBase):
    async def get(self, user_id: int, *, params: dict[str, Any] | None = None) -> User:
        payload = await self.client.items.get("User", user_id, params=params)
        return User.model_validate(payload)

    async def list(self, *, params: dict[str, Any] | None = None) -> list[User]:
        payload = await self.client.items.list("User", params=params)
        return [User.model_validate(entry) for entry in payload]

    async def search(self, **kwargs: Any) -> Any:
        return await self.client.items.search("User", **kwargs)

    async def picture(self, user_id: int) -> bytes:
        path = self.client._user_picture_path(user_id)
        data = await self.client._request("GET", path, headers={"Accept": "application/octet-stream"})
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        return bytes(str(data), "utf-8")
