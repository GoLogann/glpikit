from __future__ import annotations

import json
from collections import defaultdict

import httpx

from glpikit import GLPI, AsyncGLPI
from glpikit.transport import AsyncTransport, SyncTransport


def _sync_transport(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return SyncTransport(base_url="https://glpi.local", client=client)


def _async_transport(handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return AsyncTransport(base_url="https://glpi.local", client=client)


def test_search_options_cache_ttl() -> None:
    calls = {"search_options": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/listSearchOptions/Ticket":
            calls["search_options"] += 1
            return httpx.Response(200, json={"1": {"id": 1, "name": "Name", "uid": "Ticket.name"}})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=_sync_transport(handler),
    )

    first = glpi.items.list_search_options("Ticket")
    second = glpi.items.list_search_options("Ticket")

    assert first == second
    assert calls["search_options"] == 1


def test_iter_all_and_iter_search() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/User":
            page_range = request.url.params.get("range")
            if page_range == "0-1":
                return httpx.Response(200, json=[{"id": 1}, {"id": 2}])
            if page_range == "2-3":
                return httpx.Response(200, json=[{"id": 3}])
            return httpx.Response(200, json=[])
        if request.url.path == "/apirest.php/search/Ticket":
            page_range = request.url.params.get("range")
            if page_range == "0-1":
                return httpx.Response(200, json={"totalcount": 3, "count": 2, "data": [{"id": 1}, {"id": 2}]})
            if page_range == "2-3":
                return httpx.Response(200, json={"totalcount": 3, "count": 1, "data": [{"id": 3}]})
            return httpx.Response(200, json={"totalcount": 3, "count": 0, "data": []})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=_sync_transport(handler),
    )

    users = list(glpi.items.iter_all("User", page_size=2))
    assert [u.id for u in users] == [1, 2, 3]

    rows = list(glpi.items.iter_search("Ticket", page_size=2))
    assert [r["id"] for r in rows] == [1, 2, 3]


def test_bulk_create_partial_retry() -> None:
    calls = defaultdict(int)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/Computer" and request.method == "POST":
            payload = json.loads(request.content.decode("utf-8"))
            name = payload["input"]["name"]
            calls[name] += 1
            if name == "always_bad":
                return httpx.Response(500, json={"message": "boom"})
            if name == "flaky" and calls[name] == 1:
                return httpx.Response(500, json={"message": "retry me"})
            return httpx.Response(200, json={"id": calls[name], "name": name})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=_sync_transport(handler),
    )

    report = glpi.items.bulk_create(
        "Computer",
        [{"name": "ok"}, {"name": "flaky"}, {"name": "always_bad"}],
        retries=1,
    )

    assert report.total == 3
    assert report.succeeded == 2
    assert report.failed == 1


async def test_async_iter_search_and_cache() -> None:
    calls = {"options": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/listSearchOptions/User":
            calls["options"] += 1
            return httpx.Response(200, json={"1": {"id": 1, "name": "Name"}})
        if request.url.path == "/apirest.php/search/User":
            return httpx.Response(200, json={"totalcount": 1, "count": 1, "data": [{"id": 7}]})
        return httpx.Response(404, json={"message": "not found"})

    glpi = AsyncGLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=_async_transport(handler),
    )

    await glpi.items.list_search_options("User")
    await glpi.items.list_search_options("User")
    rows = await glpi.items.iter_search("User", page_size=10)

    assert calls["options"] == 1
    assert rows[0]["id"] == 7

    await glpi.close()


def test_search_result_metadata_single_item_lists_are_coerced() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/search/Ticket":
            return httpx.Response(
                200,
                json={
                    "totalcount": [1],
                    "count": [1],
                    "sort": [1],
                    "order": ["ASC"],
                    "data": [{"id": 1}],
                },
            )
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=_sync_transport(handler),
    )

    result = glpi.items.search("Ticket")
    assert result.totalcount == 1
    assert result.count == 1
    assert result.sort == 1
    assert result.order == "ASC"
