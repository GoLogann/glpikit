"""Legacy v1 config helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def get_config(client: GLPI) -> object:
    return client.raw.get("/apirest.php/getGlpiConfig")
