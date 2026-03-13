"""Serialization helpers."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def model_dump(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(exclude_none=True, by_alias=True)
    return value


def to_payload(data: dict[str, Any]) -> dict[str, Any]:
    return {key: model_dump(value) for key, value in data.items() if value is not None}
