"""Legacy v1 generic item wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def get_item(client: GLPI, itemtype: str, item_id: int) -> object:
    return client.items.get(itemtype, item_id)
