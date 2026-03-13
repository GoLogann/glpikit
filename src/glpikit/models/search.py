"""Search models."""

from __future__ import annotations

from typing import Any

from pydantic import Field, field_validator

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

    @field_validator("totalcount", "count", "sort", mode="before")
    @classmethod
    def _coerce_int_metadata(cls, value: Any) -> Any:
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return value

    @field_validator("order", mode="before")
    @classmethod
    def _coerce_order(cls, value: Any) -> Any:
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        return value
