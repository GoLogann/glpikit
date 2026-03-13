"""Spec-driven contract helpers for v2 operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .openapi import OpenAPIOperation, build_operation_index


@dataclass(slots=True)
class ContractCase:
    operation_id: str
    method: str
    path: str
    kwargs: dict[str, Any]


def build_minimal_kwargs(operation: OpenAPIOperation) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}
    for name in operation.path_params:
        kwargs[name] = 1
    for name in operation.required_query_params:
        kwargs[name] = "1"
    for name in operation.required_header_params:
        kwargs[name] = "x"
    for name in operation.required_cookie_params:
        kwargs[name] = "x"

    if operation.request_body_required:
        if "application/json" in operation.request_content_types or not operation.request_content_types:
            kwargs["json"] = {}
        elif "application/x-www-form-urlencoded" in operation.request_content_types:
            kwargs["data"] = {}
        else:
            kwargs["data"] = b""
    return kwargs


def build_contract_cases(openapi: dict[str, Any]) -> list[ContractCase]:
    operations = build_operation_index(openapi)
    cases: list[ContractCase] = []
    for operation_id, operation in operations.items():
        cases.append(
            ContractCase(
                operation_id=operation_id,
                method=operation.method,
                path=operation.path,
                kwargs=build_minimal_kwargs(operation),
            )
        )
    return sorted(cases, key=lambda item: item.operation_id)
