"""Adapters between OpenAPI operations and idiomatic resource-like calls."""

from .resources import AsyncV2ResourceAdapter, V2ResourceAdapter

__all__ = [
    "V2ResourceAdapter",
    "AsyncV2ResourceAdapter",
]
