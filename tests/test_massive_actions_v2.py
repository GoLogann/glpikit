from __future__ import annotations

import json
from typing import Any

import httpx

from glpikit import GLPI, AsyncGLPI
from glpikit.transport import AsyncTransport, SyncTransport


def _sync_transport(handler: Any) -> SyncTransport:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return SyncTransport(base_url="https://glpi.local", client=client)


def _async_transport(handler: Any) -> AsyncTransport:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return AsyncTransport(base_url="https://glpi.local", client=client)


def _openapi_massive() -> dict[str, Any]:
    return {
        "openapi": "3.0.0",
        "paths": {
            "/massive/{itemtype}": {
                "get": {
                    "operationId": "listMassiveActionsTicket",
                    "parameters": [
                        {"name": "itemtype", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                },
                "post": {
                    "operationId": "applyMassiveActionTicket",
                    "parameters": [
                        {"name": "itemtype", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                },
            }
        },
    }


def _openapi_massive_ranked() -> dict[str, Any]:
    return {
        "openapi": "3.0.0",
        "paths": {
            "/bulk/{scope}/{itemtype}": {
                "get": {
                    "operationId": "bulkMassiveList",
                    "parameters": [
                        {"name": "scope", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "itemtype", "in": "path", "required": True, "schema": {"type": "string"}},
                    ],
                },
                "post": {
                    "operationId": "bulkMassiveApply",
                    "parameters": [
                        {"name": "scope", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "itemtype", "in": "path", "required": True, "schema": {"type": "string"}},
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                },
            },
            "/massive/{itemtype}": {
                "get": {
                    "operationId": "listMassiveActionsTicket",
                    "parameters": [
                        {"name": "itemtype", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                },
                "post": {
                    "operationId": "applyMassiveActionTicket",
                    "parameters": [
                        {"name": "itemtype", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"input": {"type": "object"}},
                                }
                            }
                        },
                    },
                },
            },
        },
    }


def test_sync_massive_actions_v2_best_effort() -> None:
    seen: dict[str, Any] = {}
    openapi = _openapi_massive()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/v2/massive/Ticket" and request.method == "GET":
            return httpx.Response(200, json={"actions": ["delete"]})
        if request.url.path == "/api.php/v2/massive/Ticket" and request.method == "POST":
            seen["payload"] = json.loads(request.read().decode("utf-8"))
            return httpx.Response(200, json={"done": True})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_sync_transport(handler),
    )

    listed = glpi.massive_actions.list("Ticket")
    assert listed["actions"] == ["delete"]

    applied = glpi.massive_actions.apply("Ticket", action="delete", ids=[1, 2])
    assert applied["done"] is True
    assert seen["payload"]["action"] == "delete"


def test_sync_massive_actions_v2_deterministic_selection_and_input_wrapping() -> None:
    seen: dict[str, Any] = {"paths": []}
    openapi = _openapi_massive_ranked()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        seen["paths"].append((request.method, request.url.path))
        if request.url.path == "/api.php/v2/massive/Ticket" and request.method == "GET":
            return httpx.Response(200, json={"actions": ["assign"]})
        if request.url.path == "/api.php/v2/massive/Ticket" and request.method == "POST":
            seen["payload"] = json.loads(request.read().decode("utf-8"))
            return httpx.Response(200, json={"done": True})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_sync_transport(handler),
    )

    listed = glpi.massive_actions.list("Ticket")
    assert listed["actions"] == ["assign"]

    applied = glpi.massive_actions.apply("Ticket", action="assign", ids=[4], parameters={"group_id": 2})
    assert applied["done"] is True
    assert ("GET", "/api.php/v2/massive/Ticket") in seen["paths"]
    assert ("POST", "/api.php/v2/massive/Ticket") in seen["paths"]
    assert seen["payload"]["input"]["action"] == "assign"
    assert seen["payload"]["input"]["ids"] == [4]


async def test_async_massive_actions_v2_best_effort() -> None:
    openapi = _openapi_massive()

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/v2/massive/Ticket" and request.method == "GET":
            return httpx.Response(200, json={"actions": ["assign"]})
        if request.url.path == "/api.php/v2/massive/Ticket" and request.method == "POST":
            return httpx.Response(200, json={"done": True})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=_async_transport(handler),
    )

    listed = await glpi.massive_actions.list("Ticket")
    assert listed["actions"] == ["assign"]

    applied = await glpi.massive_actions.apply("Ticket", action="assign", ids=[9])
    assert applied["done"] is True

    await glpi.close()
