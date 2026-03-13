"""Legacy v1 search wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def search(client: GLPI, itemtype: str, **kwargs: object) -> object:
    return client.items.search(itemtype, **kwargs)
