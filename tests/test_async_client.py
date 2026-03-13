from __future__ import annotations

import httpx

from glpikit import AsyncGLPI
from glpikit.transport import AsyncTransport


def make_transport(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return AsyncTransport(base_url="https://glpi.local", client=client)


async def test_async_v2_flow() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "access", "expires_in": 3600})
        if request.url.path == "/api.php/v2/Ticket/22":
            assert request.headers["authorization"] == "Bearer access"
            return httpx.Response(200, json={"id": 22, "name": "Async ticket"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=make_transport(handler),
    )

    ticket = await glpi.tickets.get(22)
    assert ticket.id == 22

    await glpi.close()


async def test_async_search_builder() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/search/Ticket":
            return httpx.Response(200, json={"totalcount": 1, "count": 1, "data": [{"id": 77}]})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=make_transport(handler),
    )

    result = await glpi.search("Ticket").where("name", "contains", "foo").limit(5).run()
    assert result.totalcount == 1

    await glpi.close()


async def test_async_iterators_stream_results() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/search/Ticket":
            page_range = request.url.params.get("range")
            if page_range == "0-1":
                return httpx.Response(200, json={"totalcount": 3, "count": 2, "data": [{"id": 1}, {"id": 2}]})
            if page_range == "2-3":
                return httpx.Response(200, json={"totalcount": 3, "count": 1, "data": [{"id": 3}]})
            return httpx.Response(200, json={"totalcount": 0, "count": 0, "data": []})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=make_transport(handler),
    )

    ids = []
    async for row in glpi.search("Ticket").where("name", "contains", "foo").aiter(page_size=2):
        ids.append(row["id"])
    assert ids == [1, 2, 3]

    await glpi.close()


async def test_async_graphql_capability_probe_absent_endpoint() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/api.php/GraphQL":
            return httpx.Response(404, json={"message": "not found"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=make_transport(handler),
    )

    assert await glpi.supports_graphql_async() is False

    await glpi.close()


async def test_async_auto_mode_fallback_from_v2_to_v1() -> None:
    seen: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.path)
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(401, json={"message": "oauth failed"})
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/Ticket/10":
            return httpx.Response(200, json={"id": 10, "name": "fallback"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="auto",
        auth={
            "client_id": "cid",
            "client_secret": "secret",
            "username": "u",
            "password": "p",
            "user_token": "token-v1",
        },
        transport=make_transport(handler),
    )

    ticket = await glpi.items.get("Ticket", 10)
    assert ticket.id == 10
    assert glpi.mode == "v1"
    assert "/api.php/oauth/token" in seen
    assert "/apirest.php/Ticket/10" in seen

    await glpi.close()


async def test_async_capabilities_include_plugin_itemtypes() -> None:
    openapi = {
        "openapi": "3.0.0",
        "paths": {
            "/Ticket/{id}": {
                "get": {
                    "operationId": "getTicket",
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                }
            },
            "/PluginAcmeAsset/{id}": {
                "get": {
                    "operationId": "getPluginAcmeAsset",
                    "parameters": [{"name": "id", "in": "path", "required": True}],
                }
            },
        },
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "access", "expires_in": 3600})
        if request.url.path == "/api.php/doc/openapi.json":
            return httpx.Response(200, json=openapi)
        if request.url.path == "/api.php/GraphQL":
            return httpx.Response(200, json={"data": {"__typename": "Query"}})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={"client_id": "cid", "client_secret": "secret", "username": "u", "password": "p"},
        transport=make_transport(handler),
    )

    caps = await glpi.capabilities_async()
    assert caps["supports_v2"] is True
    assert "PluginAcmeAsset" in caps["known_itemtypes"]
    assert "PluginAcmeAsset" in caps["plugin_itemtypes"]
    assert caps["itemtype_count"] >= 1

    await glpi.close()
