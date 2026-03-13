"""Common model primitives."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class GLPIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    def to_llm_context(self) -> dict[str, Any]:
        return self.model_dump(exclude_none=True, by_alias=True)


class SessionInfo(GLPIModel):
    session_token: str | None = None
    user: str | None = None
    glpi_use_mode: int | None = None


class Timestamped(GLPIModel):
    date_creation: datetime | None = None
    date_mod: datetime | None = None
