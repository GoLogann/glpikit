"""Legacy user wrappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def picture(client: GLPI, user_id: int) -> bytes:
    return client.users.picture(user_id)
