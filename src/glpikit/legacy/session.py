"""Legacy v1 session helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from glpikit.models import SessionInfo

if TYPE_CHECKING:
    from glpikit.client import GLPI


def get_session_info(client: GLPI) -> SessionInfo:
    payload = client.raw.get("/apirest.php/getFullSession")
    if isinstance(payload, dict):
        return SessionInfo.model_validate(payload)
    return SessionInfo()
