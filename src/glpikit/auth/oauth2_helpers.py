"""OAuth2 helper utilities including PKCE."""

from __future__ import annotations

import base64
import hashlib
import secrets
from urllib.parse import urlencode


def generate_code_verifier(length: int = 64) -> str:
    if length < 43 or length > 128:
        raise ValueError("PKCE code_verifier length must be between 43 and 128")
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def build_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def generate_pkce_pair(length: int = 64) -> tuple[str, str]:
    verifier = generate_code_verifier(length)
    return verifier, build_code_challenge(verifier)


def build_authorization_url(
    *,
    authorize_url: str,
    client_id: str,
    redirect_uri: str,
    scope: str | None = None,
    state: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str = "S256",
    extra_params: dict[str, str] | None = None,
) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    if scope:
        params["scope"] = scope
    if state:
        params["state"] = state
    if code_challenge:
        params["code_challenge"] = code_challenge
        params["code_challenge_method"] = code_challenge_method
    if extra_params:
        params.update(extra_params)

    separator = "&" if "?" in authorize_url else "?"
    return f"{authorize_url}{separator}{urlencode(params)}"
