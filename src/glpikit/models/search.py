"""Search models."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from .common import GLPIModel


class SearchOption(GLPIModel):
    id: int | str
    uid: str | None = None
    name: str | None = None
    datatype: str | None = None


class SearchCriterion(GLPIModel):
    field: int | str
    searchtype: str = Field(default="contains")
    value: Any = None
    link: str | None = None


class SearchResult(GLPIModel):
    totalcount: int | None = None
    count: int | None = None
    sort: int | None = None
    order: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
