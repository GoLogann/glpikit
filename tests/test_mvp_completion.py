from __future__ import annotations

import io
import logging
from typing import Any

import httpx

from glpikit import GLPI
from glpikit.ai import (
    add_followup_tool,
    create_ticket_tool,
    get_entity_tool,
    get_ticket_tool,
    search_ticket_tool,
    search_user_tool,
    update_ticket_tool,
)
from glpikit.transport import SyncTransport, build_observability_hooks


class _SearchChain:
    def __init__(self, itemtype: str) -> None:
        self.itemtype = itemtype
        self.last_query: str | None = None
        self.last_limit: int | None = None

    def where(self, _field: str, _operator: str, value: str) -> "_SearchChain":
        self.last_query = value
        return self

    def limit(self, limit: int) -> "_SearchChain":
        self.last_limit = limit
        return self

    def run(self) -> dict[str, Any]:
        return {
            "itemtype": self.itemtype,
            "query": self.last_query,
            "limit": self.last_limit,
        }


class _FakeTickets:
    def __init__(self) -> None:
        self.created: dict[str, Any] | None = None
        self.updated: tuple[int, dict[str, Any]] | None = None
        self.followup: tuple[int, str] | None = None

    def create(self, **kwargs: Any) -> dict[str, Any]:
        self.created = kwargs
        return {"id": 11, **kwargs}

    def get(self, ticket_id: int) -> dict[str, Any]:
        return {"id": ticket_id, "name": "ticket"}

    def update(self, ticket_id: int, **kwargs: Any) -> dict[str, Any]:
        self.updated = (ticket_id, kwargs)
        return {"id": ticket_id, **kwargs}

    def add_followup(self, ticket_id: int, content: str) -> dict[str, Any]:
        self.followup = (ticket_id, content)
        return {"ticket_id": ticket_id, "content": content}


class _FakeEntities:
    def get(self, entity_id: int) -> dict[str, Any]:
        return {"id": entity_id, "name": "Entity"}


class _FakeGLPI:
    def __init__(self) -> None:
        self.tickets = _FakeTickets()
        self.entities = _FakeEntities()

    def search(self, itemtype: str) -> _SearchChain:
        return _SearchChain(itemtype)


def _make_transport(handler: Any) -> SyncTransport:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return SyncTransport(base_url="https://glpi.local", client=client)


def test_ai_tools_full_set() -> None:
    fake = _FakeGLPI()

    assert create_ticket_tool(fake)(title="Titulo", description="Descricao") == {
        "id": 11,
        "title": "Titulo",
        "description": "Descricao",
    }
    assert get_ticket_tool(fake)(ticket_id=5)["id"] == 5
    assert update_ticket_tool(fake)(ticket_id=7, title="Novo")["title"] == "Novo"
    assert add_followup_tool(fake)(ticket_id=7, content="ok")["ticket_id"] == 7
    assert search_ticket_tool(fake)(query="mail", limit=3)["itemtype"] == "Ticket"
    assert search_user_tool(fake)(query="ana", limit=2)["itemtype"] == "User"
    assert get_entity_tool(fake)(entity_id=8)["id"] == 8


def test_v2_openapi_operation_call_and_capabilities() -> None:
    captured: dict[str, Any] = {}

    openapi = {
        "openapi": "3.0.0",
        "paths": {
            "/Ticket/{id}": {
                "get": {
                    "operationId": "getTicket",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}},
                        {"name": "expand", "in": "query", "schema": {"type": "integer"}},
                    ],
                }
            }
        },
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/v2/Ticket/42":
            captured["query"] = dict(request.url.params)
            return httpx.Response(200, json={"id": 42, "name": "Ticket from op"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_make_transport(handler),
    )

    result = glpi.v2.call("getTicket", id=42, expand=1)
    assert result["id"] == 42
    assert captured["query"].get("expand") == "1"
    assert glpi.supports_itemtype("Ticket") is True

    capabilities = glpi.capabilities()
    assert capabilities["supports_v2"] is True
    assert capabilities.get("openapi_loaded") is True
    assert capabilities.get("v2_operations", 0) >= 1


def test_plugin_itemtype_resource() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/PluginMyThing/1":
            return httpx.Response(200, json={"id": 1, "name": "plugin item"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=_make_transport(handler),
    )

    item = glpi.plugin("PluginMyThing").get(1)
    assert item["id"] == 1


def test_observability_hooks_add_correlation_and_sanitize_tokens() -> None:
    stream = io.StringIO()
    logger = logging.getLogger("glpikit-test-observability")
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)

    on_request, on_response = build_observability_hooks(logger=logger)

    request = httpx.Request("GET", "https://example.test/resource", headers={"Authorization": "Bearer abc"})
    on_request(request)
    response = httpx.Response(200, request=request)
    on_response(response)

    logs = stream.getvalue()
    assert "X-Correlation-ID" in request.headers
    assert "***" in logs
