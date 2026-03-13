"""Helpers for chunked bulk operations with partial retry."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Iterable
from typing import Any, TypeVar

from glpikit.models.bulk import BulkItemResult, BulkReport

T = TypeVar("T")
R = TypeVar("R")


def chunked(items: Iterable[T], chunk_size: int) -> list[list[T]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")
    chunks: list[list[T]] = []
    current: list[T] = []
    for item in items:
        current.append(item)
        if len(current) >= chunk_size:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks


def process_bulk(
    items: Iterable[T],
    fn: Callable[[T], R],
    *,
    retries: int = 1,
) -> BulkReport:
    results: list[BulkItemResult] = []
    for item in items:
        attempts = 0
        error: str | None = None
        result: Any = None
        success = False
        while attempts < max(1, retries + 1):
            attempts += 1
            try:
                result = fn(item)
                success = True
                error = None
                break
            except Exception as exc:  # pragma: no cover - caller-specific exceptions
                error = str(exc)
        results.append(
            BulkItemResult(
                item=item,
                success=success,
                result=result,
                error=error,
                attempts=attempts,
            )
        )

    succeeded = sum(1 for entry in results if entry.success)
    failed = len(results) - succeeded
    return BulkReport(total=len(results), succeeded=succeeded, failed=failed, items=results)


async def process_bulk_async(
    items: Iterable[T],
    fn: Callable[[T], Awaitable[R]],
    *,
    retries: int = 1,
) -> BulkReport:
    results: list[BulkItemResult] = []
    for item in items:
        attempts = 0
        error: str | None = None
        result: Any = None
        success = False
        while attempts < max(1, retries + 1):
            attempts += 1
            try:
                result = await fn(item)
                success = True
                error = None
                break
            except Exception as exc:  # pragma: no cover - caller-specific exceptions
                error = str(exc)
                await asyncio.sleep(0)
        results.append(
            BulkItemResult(
                item=item,
                success=success,
                result=result,
                error=error,
                attempts=attempts,
            )
        )

    succeeded = sum(1 for entry in results if entry.success)
    failed = len(results) - succeeded
    return BulkReport(total=len(results), succeeded=succeeded, failed=failed, items=results)
