from __future__ import annotations

from typing import Any

import httpx
import pytest
from pydantic import ValidationError

from glpikit import GLPI, AsyncGLPI
from glpikit.transport import AsyncTransport, SyncTransport


def _sync_transport(handler: Any) -> SyncTransport:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return SyncTransport(base_url="https://glpi.local", client=client)


def _async_transport(handler: Any) -> AsyncTransport:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return AsyncTransport(base_url="https://glpi.local", client=client)


def _openapi_fixture() -> dict[str, Any]:
    return {
        "openapi": "3.0.0",
        "paths": {
            "/Ticket": {
                "get": {"operationId": "listTickets"},
                "post": {
                    "operationId": "createTicket",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                },
            },
            "/Ticket/{id}": {
                "get": {
                    "operationId": "getTicket",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                },
                "put": {
                    "operationId": "updateTicket",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                },
                "delete": {
                    "operationId": "deleteTicket",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                },
            },
            "/PluginMyThing/{id}": {
                "get": {
                    "operationId": "getPluginMyThing",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                }
            },
        },
    }


def test_v2_generated_dynamic_calls() -> None:
    openapi = _openapi_fixture()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/v2/Ticket/7":
            return httpx.Response(200, json={"id": 7, "name": "Ticket 7"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_sync_transport(handler),
    )

    assert glpi.v2.generated.has("getTicket") is True
    payload = glpi.v2.generated.getTicket(id=7)
    assert payload["id"] == 7


def test_v2_generated_request_validation_and_input_model() -> None:
    openapi = _openapi_fixture()
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/v2/Ticket/8" and request.method == "PUT":
            seen["body"] = request.read().decode("utf-8")
            return httpx.Response(200, json={"id": 8, "updated": True})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_sync_transport(handler),
    )

    model = glpi.v2.generated.input_model("updateTicket")
    assert model is not None

    with pytest.raises(ValidationError):
        glpi.v2.generated.updateTicket(id=8)

    with pytest.raises(ValidationError):
        glpi.v2.generated.updateTicket(id=8, json={"name": "x"}, unexpected=True)

    payload = glpi.v2.generated.updateTicket(id="8", json={"name": "x"})
    assert payload["updated"] is True
    assert seen["body"] == '{"name":"x"}'


def test_v2_adapter_crud_mapping() -> None:
    openapi = _openapi_fixture()
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        seen.append((request.method, request.url.path))
        if request.method == "GET" and request.url.path == "/api.php/v2/Ticket":
            return httpx.Response(200, json=[{"id": 1}])
        if request.method == "GET" and request.url.path == "/api.php/v2/Ticket/1":
            return httpx.Response(200, json={"id": 1})
        if request.method == "POST" and request.url.path == "/api.php/v2/Ticket":
            return httpx.Response(200, json={"id": 2})
        if request.method == "PUT" and request.url.path == "/api.php/v2/Ticket/1":
            return httpx.Response(200, json={"id": 1, "updated": True})
        if request.method == "DELETE" and request.url.path == "/api.php/v2/Ticket/1":
            return httpx.Response(200, json={"deleted": True})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_sync_transport(handler),
    )

    adapter = glpi.v2.adapter("Ticket")
    ops = adapter.operations()
    assert set(ops.keys()) >= {"list", "get", "create", "update", "delete"}

    assert adapter.list()[0]["id"] == 1
    assert adapter.get(id=1)["id"] == 1
    assert adapter.create(json={"name": "x"})["id"] == 2
    assert adapter.update(id=1, json={"name": "y"})["updated"] is True
    assert adapter.delete(id=1)["deleted"] is True
    assert ("DELETE", "/api.php/v2/Ticket/1") in seen


def test_v2_plugins_discovery_from_openapi() -> None:
    openapi = _openapi_fixture()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_sync_transport(handler),
    )

    plugins = glpi.discover_plugins()
    assert "MyThing" in plugins
    capabilities = glpi.capabilities()
    assert "PluginMyThing" in capabilities["known_itemtypes"]
    assert "PluginMyThing" in capabilities["plugin_itemtypes"]


async def test_async_v2_generated_dynamic_calls() -> None:
    openapi = _openapi_fixture()

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/v2/Ticket/9":
            return httpx.Response(200, json={"id": 9})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_async_transport(handler),
    )

    call = glpi.v2.generated.getTicket
    payload = await call(id=9)
    assert payload["id"] == 9

    await glpi.close()
