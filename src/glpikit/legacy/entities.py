"""Legacy v1 entities helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def list_entities(client: GLPI) -> object:
    return client.raw.get("/apirest.php/getMyEntities")
