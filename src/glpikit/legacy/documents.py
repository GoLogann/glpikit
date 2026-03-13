"""Legacy v1 document wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def upload(client: GLPI, **kwargs: object) -> object:
    return client.documents.upload(**kwargs)


def download(client: GLPI, document_id: int, *, to: str | None = None) -> bytes:
    return client.documents.download(document_id, to=to)
