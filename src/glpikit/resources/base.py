"""Base classes for resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from glpikit.async_client import AsyncGLPI
    from glpikit.client import GLPI


class ResourceBase:
    def __init__(self, client: GLPI) -> None:
        self.client = client

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
        skip_auth: bool = False,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        return self.client._request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
            skip_auth=skip_auth,
            confirmed=confirmed,
            dry_run=dry_run,
        )


class AsyncResourceBase:
    def __init__(self, client: AsyncGLPI) -> None:
        self.client = client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
        skip_auth: bool = False,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        return await self.client._request(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
            skip_auth=skip_auth,
            confirmed=confirmed,
            dry_run=dry_run,
        )
