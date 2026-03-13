from __future__ import annotations

import json
from pathlib import Path

import httpx

from glpikit import GLPI
from glpikit.v2 import build_contract_cases
from glpikit.v2.contract import build_minimal_kwargs
from glpikit.v2.openapi import build_operation_index

FIXTURE = Path(__file__).parent / "fixtures" / "openapi_contract.json"


def _load_openapi() -> dict:
    return json.loads(FIXTURE.read_text())


def _transport(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    from glpikit.transport import SyncTransport

    return SyncTransport(base_url="https://glpi.local", client=client)


def test_build_operation_index_metadata() -> None:
    openapi = _load_openapi()
    index = build_operation_index(openapi)

    op = index["getTicket"]
    assert "id" in op.path_params
    assert "expand" in op.required_query_params
    assert "X-Tenant" in op.required_header_params
    assert "session" in op.required_cookie_params


def test_build_contract_cases() -> None:
    openapi = _load_openapi()
    cases = build_contract_cases(openapi)
    assert {case.operation_id for case in cases} == {"getTicket", "createTicket", "updateTicket"}

    index = build_operation_index(openapi)
    minimal = build_minimal_kwargs(index["createTicket"])
    assert "json" in minimal


def test_contract_execute_all_operations() -> None:
    openapi = _load_openapi()
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, str(request.url.query), dict(request.headers)))
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.method == "GET" and request.url.path == "/api.php/v2/Ticket/1":
            return httpx.Response(200, json={"id": 1, "name": "Ticket", "state": "open"})
        if request.method == "POST" and request.url.path == "/api.php/v2/Ticket":
            return httpx.Response(201, json={"id": 2, "created": True})
        if request.method == "PUT" and request.url.path == "/api.php/v2/Ticket/1":
            return httpx.Response(200, json={"id": 1, "updated": True})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_transport(handler),
    )

    for operation_id in glpi.v2.operations():
        kwargs = build_minimal_kwargs(glpi.v2._operations[operation_id])
        kwargs.setdefault("id", 1)
        if operation_id == "getTicket":
            kwargs["expand"] = 1
            kwargs["X-Tenant"] = "tenant"
            kwargs["session"] = "cookie123"
        result = glpi.v2.call(operation_id, **kwargs)
        assert result is not None

    typed = glpi.v2.call_typed(
        "getTicket",
        id=1,
        expand=1,
        **{"X-Tenant": "tenant", "session": "cookie123"},
    )
    assert typed.id == 1
    assert typed.name == "Ticket"

    assert any(path == "/api.php/v2/Ticket/1" for _, path, _, _ in seen)
