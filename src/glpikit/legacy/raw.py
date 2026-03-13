"""Legacy raw wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def request(client: GLPI, method: str, path: str, **kwargs: object) -> object:
    return client.raw.request(method, path, **kwargs)
