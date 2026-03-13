"""Pagination helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Sequence, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class Page(Generic[T]):
    items: Sequence[T]
    total: int | None = None
    start: int | None = None
    limit: int | None = None
