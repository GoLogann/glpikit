"""Retry policy."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_factor: float = 0.3
    retry_on_status: set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})

    def should_retry_status(self, status_code: int) -> bool:
        return status_code in self.retry_on_status

    def backoff_seconds(self, attempt_number: int) -> float:
        return self.backoff_factor * (2 ** max(0, attempt_number - 1))
