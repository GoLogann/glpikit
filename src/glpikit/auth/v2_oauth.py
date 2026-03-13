"""OAuth2 auth for GLPI REST v2."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from glpikit.auth.base import AsyncAuthStrategy, SyncAuthStrategy
from glpikit.errors import OAuthError

if TYPE_CHECKING:
    from glpikit.transport.async_ import AsyncTransport
    from glpikit.transport.sync import SyncTransport


class V2OAuthAuth(SyncAuthStrategy):
    def __init__(self, auth: dict[str, Any], token_path: str = "/api.php/oauth/token") -> None:
        self.auth = auth
        self.token_path = token_path
        self.access_token: str | None = None
        self.refresh_token: str | None = auth.get("refresh_token")
        self.expires_at: float = 0.0
        self._retry_used = False

    def _is_expired(self) -> bool:
        if not self.access_token:
            return True
        return time.time() >= max(0.0, self.expires_at - 30)

    def prepare(self, transport: SyncTransport) -> None:
        if not self._is_expired():
            return
        if self.refresh_token:
            try:
                self._refresh(transport)
                return
            except OAuthError:
                pass
        self._login(transport)

    def _token_request(self, transport: SyncTransport, data: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = dict(data)
        client_id = self.auth.get("client_id")
        client_secret = self.auth.get("client_secret")
        if client_id:
            payload.setdefault("client_id", client_id)
        if client_secret:
            payload.setdefault("client_secret", client_secret)
        return transport.request(
            "POST",
            self.token_path,
            data=payload,
            headers=headers,
            skip_auth=True,
        )

    def _consume_token_response(self, response: dict[str, Any]) -> None:
        access_token = response.get("access_token")
        if not access_token:
            raise OAuthError("OAuth token endpoint did not return access_token", payload=response)
        self.access_token = access_token
        self.refresh_token = response.get("refresh_token", self.refresh_token)
        expires_in = response.get("expires_in")
        self.expires_at = time.time() + float(expires_in or 3600)
        self._retry_used = False

    def _login(self, transport: SyncTransport) -> None:
        authorization_code = self.auth.get("authorization_code") or self.auth.get("code")
        redirect_uri = self.auth.get("redirect_uri")
        code_verifier = self.auth.get("code_verifier")
        username = self.auth.get("username")
        password = self.auth.get("password")
        if authorization_code and redirect_uri:
            grant_data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": redirect_uri,
            }
            if code_verifier:
                grant_data["code_verifier"] = code_verifier
        elif username and password:
            grant_data = {
                "grant_type": "password",
                "username": username,
                "password": password,
            }
        else:
            grant_data = {"grant_type": "client_credentials"}
        response = self._token_request(transport, grant_data)
        self._consume_token_response(response)

    def _refresh(self, transport: SyncTransport) -> None:
        if not self.refresh_token:
            raise OAuthError("refresh token not available")
        response = self._token_request(
            transport,
            {"grant_type": "refresh_token", "refresh_token": self.refresh_token},
        )
        self._consume_token_response(response)

    def headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    def on_unauthorized(self, transport: SyncTransport) -> bool:
        if self._retry_used:
            return False
        self._retry_used = True
        self.access_token = None
        self.prepare(transport)
        return True

    def close(self, transport: SyncTransport) -> None:
        return


class AsyncV2OAuthAuth(AsyncAuthStrategy):
    def __init__(self, auth: dict[str, Any], token_path: str = "/api.php/oauth/token") -> None:
        self.auth = auth
        self.token_path = token_path
        self.access_token: str | None = None
        self.refresh_token: str | None = auth.get("refresh_token")
        self.expires_at: float = 0.0
        self._retry_used = False

    def _is_expired(self) -> bool:
        if not self.access_token:
            return True
        return time.time() >= max(0.0, self.expires_at - 30)

    async def prepare(self, transport: AsyncTransport) -> None:
        if not self._is_expired():
            return
        if self.refresh_token:
            try:
                await self._refresh(transport)
                return
            except OAuthError:
                pass
        await self._login(transport)

    async def _token_request(self, transport: AsyncTransport, data: dict[str, Any]) -> dict[str, Any]:
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = dict(data)
        client_id = self.auth.get("client_id")
        client_secret = self.auth.get("client_secret")
        if client_id:
            payload.setdefault("client_id", client_id)
        if client_secret:
            payload.setdefault("client_secret", client_secret)
        return await transport.request(
            "POST",
            self.token_path,
            data=payload,
            headers=headers,
            skip_auth=True,
        )

    def _consume_token_response(self, response: dict[str, Any]) -> None:
        access_token = response.get("access_token")
        if not access_token:
            raise OAuthError("OAuth token endpoint did not return access_token", payload=response)
        self.access_token = access_token
        self.refresh_token = response.get("refresh_token", self.refresh_token)
        expires_in = response.get("expires_in")
        self.expires_at = time.time() + float(expires_in or 3600)
        self._retry_used = False

    async def _login(self, transport: AsyncTransport) -> None:
        authorization_code = self.auth.get("authorization_code") or self.auth.get("code")
        redirect_uri = self.auth.get("redirect_uri")
        code_verifier = self.auth.get("code_verifier")
        username = self.auth.get("username")
        password = self.auth.get("password")
        if authorization_code and redirect_uri:
            grant_data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": redirect_uri,
            }
            if code_verifier:
                grant_data["code_verifier"] = code_verifier
        elif username and password:
            grant_data = {
                "grant_type": "password",
                "username": username,
                "password": password,
            }
        else:
            grant_data = {"grant_type": "client_credentials"}
        response = await self._token_request(transport, grant_data)
        self._consume_token_response(response)

    async def _refresh(self, transport: AsyncTransport) -> None:
        if not self.refresh_token:
            raise OAuthError("refresh token not available")
        response = await self._token_request(
            transport,
            {"grant_type": "refresh_token", "refresh_token": self.refresh_token},
        )
        self._consume_token_response(response)

    def headers(self) -> dict[str, str]:
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}

    async def on_unauthorized(self, transport: AsyncTransport) -> bool:
        if self._retry_used:
            return False
        self._retry_used = True
        self.access_token = None
        await self.prepare(transport)
        return True

    async def close(self, transport: AsyncTransport) -> None:
        return
