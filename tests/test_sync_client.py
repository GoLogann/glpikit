from __future__ import annotations

from typing import Any

import httpx

from glpikit import GLPI
from glpikit.models import Ticket
from glpikit.transport import SyncTransport


def make_transport(handler: Any) -> SyncTransport:
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://glpi.local")
    return SyncTransport(base_url="https://glpi.local", client=client)


def test_auto_mode_resolution() -> None:
    glpi_v1 = GLPI(base_url="https://glpi.local", auth={"user_token": "u"}, transport=make_transport(lambda r: httpx.Response(200, json={})))
    glpi_v2 = GLPI(
        base_url="https://glpi.local",
        auth={"client_id": "id", "client_secret": "secret"},
        transport=make_transport(lambda r: httpx.Response(200, json={})),
    )
    glpi_v2_refresh = GLPI(
        base_url="https://glpi.local",
        auth={"refresh_token": "refresh"},
        transport=make_transport(lambda r: httpx.Response(200, json={})),
    )

    assert glpi_v1.mode == "v1"
    assert glpi_v2.mode == "v2"
    assert glpi_v2_refresh.mode == "v2"


def test_v1_session_headers_and_ticket_get() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path == "/apirest.php/initSession":
            assert request.headers["authorization"].startswith("user_token")
            assert request.headers["app-token"] == "app"
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/Ticket/1":
            assert request.headers["session-token"] == "sess"
            assert request.headers["app-token"] == "app"
            return httpx.Response(200, json={"id": 1, "name": "Falha e-mail", "content": "Erro auth"})
        if request.url.path == "/apirest.php/killSession":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        auth={"user_token": "user-token", "app_token": "app"},
        mode="v1",
        transport=make_transport(handler),
    )

    ticket = glpi.tickets.get(1)
    assert isinstance(ticket, Ticket)
    assert ticket.id == 1

    glpi.close()
    paths = [request.url.path for request in calls]
    assert "/apirest.php/initSession" in paths
    assert "/apirest.php/killSession" in paths


def test_v2_oauth_token_then_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "access", "expires_in": 3600})
        if request.url.path == "/api.php/v2/Ticket/10":
            assert request.headers["authorization"] == "Bearer access"
            return httpx.Response(200, json={"id": 10, "name": "OAuth ticket"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v2",
        auth={
            "client_id": "cid",
            "client_secret": "csecret",
            "username": "user",
            "password": "pass",
        },
        transport=make_transport(handler),
    )

    ticket = glpi.items.get("Ticket", 10)
    assert ticket.id == 10


def test_search_builder_flow() -> None:
    captured_search: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/search/Ticket":
            captured_search["query"] = str(request.url.query)
            return httpx.Response(200, json={"totalcount": 1, "count": 1, "data": [{"id": 1}]})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=make_transport(handler),
    )

    result = (
        glpi.search("Ticket")
        .where("name", "contains", "email")
        .and_("status", "equals", 2)
        .sort("date_mod", "desc")
        .limit(20)
        .run()
    )

    assert result.totalcount == 1
    assert "criteria" in captured_search["query"]


def test_graphql_query() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/api.php/GraphQL":
            return httpx.Response(200, json={"data": {"Ticket": [{"id": 1}]}})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=make_transport(handler),
    )

    data = glpi.graphql.query("query { Ticket { id } }")
    assert isinstance(data, dict)
    assert "Ticket" in data


def test_graphql_capability_probe_absent_endpoint() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/api.php/GraphQL":
            return httpx.Response(404, json={"message": "not found"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
        base_url="https://glpi.local",
        mode="v1",
        auth={"user_token": "u"},
        transport=make_transport(handler),
    )

    assert glpi.supports_graphql() is False


def test_auto_mode_fallback_from_v2_to_v1_after_oauth_prepare_failure() -> None:
    paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(401, json={"message": "oauth failed"})
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/Ticket/5":
            return httpx.Response(200, json={"id": 5, "name": "fallback ok"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
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

    ticket = glpi.items.get("Ticket", 5)
    assert ticket.id == 5
    assert glpi.mode == "v1"
    assert "/api.php/oauth/token" in paths
    assert "/apirest.php/initSession" in paths
    assert "/apirest.php/Ticket/5" in paths


def test_auto_mode_fallback_after_repeated_401_on_v2_request() -> None:
    attempts = {"v2": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api.php/oauth/token":
            return httpx.Response(200, json={"access_token": "access", "expires_in": 3600})
        if request.url.path == "/api.php/v2/Ticket/6":
            attempts["v2"] += 1
            return httpx.Response(401, json={"message": "expired token"})
        if request.url.path == "/apirest.php/initSession":
            return httpx.Response(200, json={"session_token": "sess"})
        if request.url.path == "/apirest.php/Ticket/6":
            return httpx.Response(200, json={"id": 6, "name": "fallback on 401"})
        return httpx.Response(404, json={"message": "not found"})

    glpi = GLPI(
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

    ticket = glpi.items.get("Ticket", 6)
    assert ticket.id == 6
    assert attempts["v2"] >= 2
    assert glpi.mode == "v1"
