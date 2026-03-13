"""Auth strategy builders."""

from __future__ import annotations

from typing import Any

from .base import AsyncAuthStrategy, SyncAuthStrategy
from .v1_session import AsyncV1SessionAuth, V1SessionAuth
from .v2_oauth import AsyncV2OAuthAuth, V2OAuthAuth


def resolve_mode(mode: str, auth: dict[str, Any]) -> str:
    normalized = mode.lower().strip()
    if normalized != "auto":
        return normalized

    oauth_hints = (
        "client_id",
        "client_secret",
        "refresh_token",
        "authorization_code",
        "code",
        "code_verifier",
    )
    if any(auth.get(key) for key in oauth_hints):
        return "v2"

    grant_type = auth.get("grant_type")
    if isinstance(grant_type, str) and grant_type.lower() in {
        "authorization_code",
        "client_credentials",
        "password",
        "refresh_token",
    }:
        return "v2"

    if auth.get("user_token") or auth.get("app_token"):
        return "v1"

    return "v1"


def build_sync_auth(mode: str, auth: dict[str, Any], token_path: str = "/api.php/oauth/token") -> SyncAuthStrategy:
    resolved = resolve_mode(mode, auth)
    if resolved == "v1":
        return V1SessionAuth(auth)
    if resolved == "v2":
        return V2OAuthAuth(auth, token_path=token_path)
    raise ValueError(f"Unsupported mode: {resolved}")


def build_async_auth(
    mode: str,
    auth: dict[str, Any],
    token_path: str = "/api.php/oauth/token",
) -> AsyncAuthStrategy:
    resolved = resolve_mode(mode, auth)
    if resolved == "v1":
        return AsyncV1SessionAuth(auth)
    if resolved == "v2":
        return AsyncV2OAuthAuth(auth, token_path=token_path)
    raise ValueError(f"Unsupported mode: {resolved}")
