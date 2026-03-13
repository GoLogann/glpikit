"""Low-level escape hatch resource."""

from __future__ import annotations

from typing import Any

from .base import AsyncResourceBase, ResourceBase


class RawResource(ResourceBase):
    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        return self._request(method, path, **kwargs)

    def get(self, path: str, *, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return self._request("GET", path, params=params, **kwargs)

    def post(self, path: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> Any:
        return self._request("POST", path, json=json, data=data, **kwargs)

    def put(self, path: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> Any:
        return self._request("PUT", path, json=json, data=data, **kwargs)

    def delete(self, path: str, *, json: Any = None, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return self._request("DELETE", path, json=json, params=params, **kwargs)


class AsyncRawResource(AsyncResourceBase):
    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        return await self._request(method, path, **kwargs)

    async def get(self, path: str, *, params: dict[str, Any] | None = None, **kwargs: Any) -> Any:
        return await self._request("GET", path, params=params, **kwargs)

    async def post(self, path: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> Any:
        return await self._request("POST", path, json=json, data=data, **kwargs)

    async def put(self, path: str, *, json: Any = None, data: Any = None, **kwargs: Any) -> Any:
        return await self._request("PUT", path, json=json, data=data, **kwargs)

    async def delete(
        self,
        path: str,
        *,
        json: Any = None,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        return await self._request("DELETE", path, json=json, params=params, **kwargs)
