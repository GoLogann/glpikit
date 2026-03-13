"""Ticket models."""

from __future__ import annotations

from pydantic import Field

from .common import GLPIModel, Timestamped


class Ticket(Timestamped):
    id: int | None = None
    name: str | None = Field(default=None, alias="title")
    content: str | None = Field(default=None, alias="description")
    status: int | None = None
    urgency: int | None = None
    impact: int | None = None
    priority: int | None = None
    entities_id: int | None = None


class Followup(GLPIModel):
    id: int | None = None
    tickets_id: int | None = None
    content: str | None = None
