"""Bulk operation models."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import GLPIModel


class BulkItemResult(GLPIModel):
    item: Any = None
    success: bool = False
    result: Any = None
    error: str | None = None
    attempts: int = 1


class BulkReport(GLPIModel):
    total: int = 0
    succeeded: int = 0
    failed: int = 0
    items: list[BulkItemResult] = Field(default_factory=list)

    def as_summary(self) -> dict[str, int]:
        return {
            "total": self.total,
            "succeeded": self.succeeded,
            "failed": self.failed,
        }
