"""User models."""

from __future__ import annotations

from .common import GLPIModel, Timestamped


class User(Timestamped):
    id: int | None = None
    name: str | None = None
    realname: str | None = None
    firstname: str | None = None
    email: str | None = None


class Profile(GLPIModel):
    id: int | None = None
    name: str | None = None


class Entity(GLPIModel):
    id: int | None = None
    name: str | None = None
