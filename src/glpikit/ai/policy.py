"""Policy engine for sensitive operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PolicyDecision:
    allowed: bool
    dry_run: bool = False
    reason: str | None = None


@dataclass(slots=True)
class PolicyRule:
    method: str
    path_contains: str | None = None
    require_confirmation: bool = False
    allow: bool = True


@dataclass(slots=True)
class PolicyEngine:
    default_allow: bool = True
    destructive_methods: set[str] = field(default_factory=lambda: {"DELETE"})
    rules: list[PolicyRule] = field(default_factory=list)

    def evaluate(
        self,
        *,
        method: str,
        path: str,
        confirmed: bool = False,
        dry_run: bool = False,
        payload: Any = None,
    ) -> PolicyDecision:
        del payload
        normalized_method = method.upper()

        for rule in self.rules:
            if rule.method.upper() != normalized_method:
                continue
            if rule.path_contains and rule.path_contains not in path:
                continue
            if rule.require_confirmation and not confirmed:
                return PolicyDecision(
                    allowed=False,
                    reason="confirmation required by policy rule",
                )
            if not rule.allow:
                return PolicyDecision(allowed=False, reason="blocked by policy rule")

        if normalized_method in self.destructive_methods and dry_run:
            return PolicyDecision(allowed=True, dry_run=True, reason="dry-run mode")

        return PolicyDecision(allowed=self.default_allow)
