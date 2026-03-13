"""Simple in-memory TTL cache."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass(slots=True)
class _Entry(Generic[V]):
    value: V
    expires_at: float


class TTLCache(Generic[K, V]):
    def __init__(self, *, ttl_seconds: float = 300.0) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[K, _Entry[V]] = {}

    def get(self, key: K) -> V | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() >= entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: K, value: V, *, ttl_seconds: float | None = None) -> None:
        ttl = self.ttl_seconds if ttl_seconds is None else ttl_seconds
        self._store[key] = _Entry(value=value, expires_at=time.time() + max(0.0, ttl))

    def delete(self, key: K) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

    def keys(self) -> list[K]:
        self._purge_expired()
        return list(self._store.keys())

    def _purge_expired(self) -> None:
        now = time.time()
        expired = [key for key, entry in self._store.items() if now >= entry.expires_at]
        for key in expired:
            self._store.pop(key, None)
