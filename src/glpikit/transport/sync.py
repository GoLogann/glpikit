"""Synchronous HTTP transport."""

from __future__ import annotations

import time
from typing import Any

import httpx

from glpikit.errors import TransportError
from glpikit.transport._parsing import parse_body, raise_for_error
from glpikit.transport.hooks import RequestHook, ResponseHook
from glpikit.transport.retry import RetryPolicy


class SyncTransport:
    def __init__(
        self,
        *,
        base_url: str,
        timeout: float = 30.0,
        retry_policy: RetryPolicy | None = None,
        headers: dict[str, str] | None = None,
        client: httpx.Client | None = None,
        request_hook: RequestHook | None = None,
        response_hook: ResponseHook | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.retry_policy = retry_policy or RetryPolicy()
        self._owns_client = client is None
        self.client = client or httpx.Client(base_url=self.base_url, timeout=timeout, headers=headers)
        self.request_hook = request_hook
        self.response_hook = response_hook

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if path.startswith("/"):
            return f"{self.base_url}{path}"
        return f"{self.base_url}/{path}"

    def request_raw(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = self._url(path)
        last_exc: Exception | None = None
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            try:
                request = self.client.build_request(
                    method,
                    url,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=headers,
                )
                if self.request_hook:
                    self.request_hook(request)
                response = self.client.send(request)
                if self.response_hook:
                    self.response_hook(response)

                if (
                    attempt < self.retry_policy.max_attempts
                    and self.retry_policy.should_retry_status(response.status_code)
                ):
                    time.sleep(self.retry_policy.backoff_seconds(attempt))
                    continue
                return response
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt >= self.retry_policy.max_attempts:
                    break
                time.sleep(self.retry_policy.backoff_seconds(attempt))

        raise TransportError("Request transport failed", payload=str(last_exc))

    def parse_response(self, response: httpx.Response) -> Any:
        payload = parse_body(response)
        if response.status_code >= 400:
            raise_for_error(response, payload)
        return payload

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: dict[str, str] | None = None,
        skip_auth: bool = False,
    ) -> Any:
        del skip_auth
        response = self.request_raw(
            method,
            path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )
        return self.parse_response(response)

    def close(self) -> None:
        if self._owns_client:
            self.client.close()
