"""Legacy v1 profiles helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from glpikit.client import GLPI


def list_profiles(client: GLPI) -> object:
    return client.raw.get("/apirest.php/getMyProfiles")
