"""GraphQL models."""

from __future__ import annotations

from typing import Any

from .common import GLPIModel


class GraphQLError(GLPIModel):
    message: str
    path: list[str | int] | None = None
    locations: list[dict[str, int]] | None = None


class GraphQLResponse(GLPIModel):
    data: dict[str, Any] | None = None
    errors: list[GraphQLError] | None = None
