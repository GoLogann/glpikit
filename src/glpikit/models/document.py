"""Document models."""

from __future__ import annotations

from .common import GLPIModel, Timestamped


class Document(Timestamped):
    id: int | None = None
    name: str | None = None
    entities_id: int | None = None
    filename: str | None = None


class UploadResult(GLPIModel):
    id: int | None = None
    message: str | None = None
