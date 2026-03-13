"""Response parsing and error mapping."""

from __future__ import annotations

from typing import Any

import httpx

from glpikit.errors import (
    AuthenticationError,
    ConflictError,
    GLPIError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    SerializationError,
    ServerError,
    ValidationError,
)


def parse_body(response: httpx.Response) -> Any:
    if response.status_code == 204:
        return {}

    content_type = response.headers.get("Content-Type", "").lower()
    if "json" in content_type:
        try:
            return response.json()
        except ValueError as exc:
            raise SerializationError(
                "Failed to decode JSON response",
                status_code=response.status_code,
                payload=response.text,
                headers=dict(response.headers),
            ) from exc

    if not response.content:
        return {}
    if "text/" in content_type:
        return response.text
    return response.content


def raise_for_error(response: httpx.Response, payload: Any) -> None:
    status = response.status_code
    message = "GLPI request failed"
    details = payload if isinstance(payload, dict) else None
    if isinstance(details, dict):
        for key in ("message", "error", "ERROR"):
            maybe = details.get(key)
            if maybe:
                message = str(maybe)
                break

    kwargs = {
        "status_code": status,
        "payload": payload,
        "headers": dict(response.headers),
    }

    if status == 401:
        raise AuthenticationError(message, **kwargs)
    if status == 403:
        raise PermissionDeniedError(message, **kwargs)
    if status == 404:
        raise NotFoundError(message, **kwargs)
    if status in {400, 422}:
        raise ValidationError(message, **kwargs)
    if status == 409:
        raise ConflictError(message, **kwargs)
    if status == 429:
        raise RateLimitError(message, **kwargs)
    if status >= 500:
        raise ServerError(message, **kwargs)
    raise GLPIError(message, **kwargs)
