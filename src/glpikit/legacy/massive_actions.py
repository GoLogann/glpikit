"""Legacy massive action wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def list_actions(client: GLPI, itemtype: str) -> object:
    return client.massive_actions.list(itemtype)
