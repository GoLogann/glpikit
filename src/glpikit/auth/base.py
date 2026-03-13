"""Authentication base strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.transport.async_ import AsyncTransport
    from glpikit.transport.sync import SyncTransport


class SyncAuthStrategy(ABC):
    @abstractmethod
    def prepare(self, transport: "SyncTransport") -> None:
        pass

    @abstractmethod
    def headers(self) -> dict[str, str]:
        pass

    @abstractmethod
    def on_unauthorized(self, transport: "SyncTransport") -> bool:
        pass

    @abstractmethod
    def close(self, transport: "SyncTransport") -> None:
        pass


class AsyncAuthStrategy(ABC):
    @abstractmethod
    async def prepare(self, transport: "AsyncTransport") -> None:
        pass

    @abstractmethod
    def headers(self) -> dict[str, str]:
        pass

    @abstractmethod
    async def on_unauthorized(self, transport: "AsyncTransport") -> bool:
        pass

    @abstractmethod
    async def close(self, transport: "AsyncTransport") -> None:
        pass
