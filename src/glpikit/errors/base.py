"""Error hierarchy for glpikit."""

from __future__ import annotations

from typing import Any


class GLPIError(Exception):
    """Base exception for all SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        payload: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload
        self.headers = headers or {}

    def to_prompt_context(self) -> dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "payload": self.payload,
        }


class AuthenticationError(GLPIError):
    pass


class SessionExpiredError(AuthenticationError):
    pass


class OAuthError(AuthenticationError):
    pass


class PermissionDeniedError(GLPIError):
    pass


class NotFoundError(GLPIError):
    pass


class ValidationError(GLPIError):
    pass


class ConflictError(GLPIError):
    pass


class RateLimitError(GLPIError):
    pass


class ServerError(GLPIError):
    pass


class TransportError(GLPIError):
    pass


class SerializationError(GLPIError):
    pass


class UnsupportedFeatureError(GLPIError):
    pass


class PolicyViolationError(GLPIError):
    pass
