from __future__ import annotations

import json
from urllib.parse import parse_qs

import httpx
import pytest

from glpikit import GLPI
from glpikit.ai import PolicyEngine, PolicyRule
from glpikit.auth import build_authorization_url, generate_pkce_pair
from glpikit.errors import PolicyViolationError
from glpikit.transport import MetricsCollector, SyncTransport, build_observability_hooks


def _transport(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return SyncTransport(base_url="https://glpi.local", client=client)


def test_policy_engine_blocks_unconfirmed_delete() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/Ticket/1":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404, json={"message": "not found"})

    engine = PolicyEngine(rules=[PolicyRule(method="DELETE", path_contains="/Ticket/", require_confirmation=True)])
    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        policy_engine=engine,
        transport=_transport(handler),
    )

    with pytest.raises(PolicyViolationError):
        glpi.items.delete("Ticket", 1)

    payload = glpi.items.delete("Ticket", 1, confirmed=True)
    assert payload["ok"] is True


def test_policy_engine_dry_run() -> None:
    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        dry_run=True,
        auth={"user_token": "u"},
        policy_engine=PolicyEngine(),
        transport=_transport(lambda request: httpx.Response(200, json={"unexpected": True})),
    )

    result = glpi.items.delete("Ticket", 9)
    assert result["dry_run"] is True


def test_oauth_authorization_code_flow_and_pkce() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            seen["token_payload"] = parse_qs(request.read().decode("utf-8"))
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/v2/Ticket/3":
            return httpx.Response(200, json={"id": 3})
        return httpx.Response(404, json={"message": "not found"})

    verifier, challenge = generate_pkce_pair()
    url = build_authorization_url(
        authorize_url="https://auth.example/authorize",
        client_id="cid",
        redirect_uri="https://localhost/callback",
        code_challenge=challenge,
        state="abc",
    )

    assert "code_challenge" in url
    assert verifier

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={
            "client_id": "cid",
            "client_secret": "secret",
            "authorization_code": "code123",
            "redirect_uri": "https://localhost/callback",
            "code_verifier": verifier,
        },
        transport=_transport(handler),
    )

    ticket = glpi.items.get("Ticket", 3)
    assert ticket.id == 3
    assert seen["token_payload"]["grant_type"][0] == "authorization_code"


def test_v2_call_typed_returns_model() -> None:
    openapi = {
        "openapi": "3.0.0",
        "paths": {
            "/Ticket/{id}": {
                "get": {
                    "operationId": "getTicket",
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                        },
                                        "required": ["id"],
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/v2/Ticket/1":
            return httpx.Response(200, json={"id": 1, "name": "Typed"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_transport(handler),
    )

    typed = glpi.v2.call_typed("getTicket", id=1)
    assert typed.id == 1
    assert typed.name == "Typed"


def test_v2_call_coerces_openapi_parameter_types() -> None:
    seen: dict[str, object] = {}
    openapi = {
        "openapi": "3.0.0",
        "paths": {
            "/Ticket/{id}": {
                "post": {
                    "operationId": "updateTicket",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}},
                        {"name": "expand", "in": "query", "required": True, "schema": {"type": "integer"}},
                        {"name": "active", "in": "query", "schema": {"type": "boolean"}},
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        },
                    },
                    "responses": {"200": {"description": "ok"}},
                }
            }
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/v2/Ticket/7":
            seen["query"] = dict(request.url.params)
            seen["body"] = request.read().decode("utf-8")
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_transport(handler),
    )

    result = glpi.v2.call(
        "updateTicket",
        id="7",
        expand="1",
        active="true",
        json='{"name":"updated"}',
    )
    assert result["ok"] is True
    assert seen["query"] == {"expand": "1", "active": "true"}
    assert seen["body"] == '{"name":"updated"}'


def test_observability_metrics_collector() -> None:
    metrics = MetricsCollector()
    on_request, on_response = build_observability_hooks(metrics_collector=metrics)

    request = httpx.Request("GET", "https://example.test/status")
    on_request(request)
    response = httpx.Response(200, request=request, text=json.dumps({"ok": True}))
    on_response(response)
    failing_request = httpx.Request("POST", "https://example.test/status")
    on_request(failing_request)
    failing_response = httpx.Response(500, request=failing_request, text=json.dumps({"ok": False}))
    on_response(failing_response)

    snapshot = metrics.snapshot()
    assert snapshot["requests_total"] == 2
    assert snapshot["failures_total"] == 1
    assert snapshot["by_status"][200] == 1
    assert snapshot["by_status"][500] == 1
    assert snapshot["by_method"]["GET"] == 1
    assert snapshot["by_method"]["POST"] == 1
    assert snapshot["max_latency_ms"] >= 0


def test_observability_event_hook_emits_request_and_response() -> None:
    events = []
    on_request, on_response = build_observability_hooks(event_hook=events.append)

    request = httpx.Request("GET", "https://example.test/tickets")
    on_request(request)
    response = httpx.Response(200, request=request)
    on_response(response)

    assert len(events) == 2
    assert events[0]["event"] == "http_request"
    assert events[1]["event"] == "http_response"
    assert events[0]["correlation_id"] == events[1]["correlation_id"]
