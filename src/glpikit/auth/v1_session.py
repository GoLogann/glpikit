"""Legacy API v1 session auth."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Any

from glpikit.auth.base import AsyncAuthStrategy, SyncAuthStrategy
from glpikit.errors import AuthenticationError, GLPIError, SessionExpiredError

if TYPE_CHECKING:
    from glpikit.transport.async_ import AsyncTransport
    from glpikit.transport.sync import SyncTransport


class V1SessionAuth(SyncAuthStrategy):
    def __init__(self, auth: dict[str, Any]) -> None:
        self.auth = auth
        self.session_token: str | None = None
        self._retry_used = False

    def _init_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        app_token = self.auth.get("app_token")
        if app_token:
            headers["App-Token"] = app_token

        user_token = self.auth.get("user_token")
        username = self.auth.get("username")
        password = self.auth.get("password")

        if user_token:
            headers["Authorization"] = f"user_token {user_token}"
        elif username and password:
            basic = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {basic}"
        else:
            raise AuthenticationError(
                "v1 auth requires user_token or username/password",
            )
        return headers

    def prepare(self, transport: SyncTransport) -> None:
        if self.session_token:
            return
        self._open_session(transport)

    def _open_session(self, transport: SyncTransport) -> None:
        response = transport.request(
            "GET",
            "/apirest.php/initSession",
            headers=self._init_headers(),
            skip_auth=True,
        )
        token = response.get("session_token")
        if not token:
            raise AuthenticationError("initSession did not return session_token", payload=response)
        self.session_token = token
        self._retry_used = False

    def headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.auth.get("app_token"):
            headers["App-Token"] = str(self.auth["app_token"])
        if self.session_token:
            headers["Session-Token"] = self.session_token
        return headers

    def on_unauthorized(self, transport: SyncTransport) -> bool:
        if self._retry_used:
            return False
        self._retry_used = True
        self.session_token = None
        self._open_session(transport)
        return True

    def close(self, transport: SyncTransport) -> None:
        if not self.session_token:
            return
        try:
            transport.request(
                "GET",
                "/apirest.php/killSession",
                headers=self.headers(),
                skip_auth=True,
            )
        except GLPIError:
            pass
        finally:
            self.session_token = None


class AsyncV1SessionAuth(AsyncAuthStrategy):
    def __init__(self, auth: dict[str, Any]) -> None:
        self.auth = auth
        self.session_token: str | None = None
        self._retry_used = False

    def _init_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        app_token = self.auth.get("app_token")
        if app_token:
            headers["App-Token"] = app_token

        user_token = self.auth.get("user_token")
        username = self.auth.get("username")
        password = self.auth.get("password")

        if user_token:
            headers["Authorization"] = f"user_token {user_token}"
        elif username and password:
            basic = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
            headers["Authorization"] = f"Basic {basic}"
        else:
            raise AuthenticationError(
                "v1 auth requires user_token or username/password",
            )
        return headers

    async def prepare(self, transport: AsyncTransport) -> None:
        if self.session_token:
            return
        await self._open_session(transport)

    async def _open_session(self, transport: AsyncTransport) -> None:
        response = await transport.request(
            "GET",
            "/apirest.php/initSession",
            headers=self._init_headers(),
            skip_auth=True,
        )
        token = response.get("session_token")
        if not token:
            raise AuthenticationError("initSession did not return session_token", payload=response)
        self.session_token = token
        self._retry_used = False

    def headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.auth.get("app_token"):
            headers["App-Token"] = str(self.auth["app_token"])
        if self.session_token:
            headers["Session-Token"] = self.session_token
        return headers

    async def on_unauthorized(self, transport: AsyncTransport) -> bool:
        if self._retry_used:
            return False
        self._retry_used = True
        self.session_token = None
        try:
            await self._open_session(transport)
        except AuthenticationError as exc:
            raise SessionExpiredError(str(exc), payload=exc.payload) from exc
        return True

    async def close(self, transport: AsyncTransport) -> None:
        if not self.session_token:
            return
        try:
            await transport.request(
                "GET",
                "/apirest.php/killSession",
                headers=self.headers(),
                skip_auth=True,
            )
        except GLPIError:
            pass
        finally:
            self.session_token = None
