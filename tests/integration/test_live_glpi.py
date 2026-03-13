from __future__ import annotations

import os

import pytest

from glpikit import GLPI


def _live_env() -> tuple[str, dict[str, str]] | None:
    base_url = os.getenv("GLPI_INTEGRATION_BASE_URL")
    if not base_url:
        return None
    auth = {}
    for key in (
        "GLPI_INTEGRATION_USER_TOKEN",
        "GLPI_INTEGRATION_APP_TOKEN",
        "GLPI_INTEGRATION_CLIENT_ID",
        "GLPI_INTEGRATION_CLIENT_SECRET",
        "GLPI_INTEGRATION_USERNAME",
        "GLPI_INTEGRATION_PASSWORD",
    ):
        value = os.getenv(key)
        if value:
            auth[key.replace("GLPI_INTEGRATION_", "").lower()] = value
    return base_url, auth


def _live_env_v1() -> tuple[str, dict[str, str]] | None:
    live = _live_env()
    if live is None:
        return None
    base_url, auth = live
    if not auth.get("user_token"):
        return None
    return base_url, auth


def _live_env_v2() -> tuple[str, dict[str, str]] | None:
    live = _live_env()
    if live is None:
        return None
    base_url, auth = live
    if not auth.get("client_id"):
        return None
    return base_url, auth


pytestmark = pytest.mark.integration


@pytest.mark.skipif(_live_env() is None, reason="GLPI integration env vars not configured")
def test_live_capabilities_and_basic_search() -> None:
    live = _live_env()
    assert live is not None
    base_url, auth = live

    mode = "v2" if auth.get("client_id") else "v1"
    glpi = GLPI(base_url=base_url, mode=mode, auth=auth)

    caps = glpi.capabilities()
    assert "supports_graphql" in caps

    # Smoke test read path only.
    result = glpi.search("Ticket").limit(1).run()
    assert result is not None

    glpi.close()


@pytest.mark.skipif(_live_env_v1() is None, reason="v1 integration env vars not configured")
def test_live_v1_search_options_and_iter() -> None:
    live = _live_env_v1()
    assert live is not None
    base_url, auth = live

    glpi = GLPI(base_url=base_url, mode="v1", auth=auth)

    options = glpi.items.list_search_options("Ticket")
    assert options is not None

    rows = list(glpi.items.iter_search("Ticket", page_size=1, max_pages=1))
    assert isinstance(rows, list)

    glpi.close()


@pytest.mark.skipif(_live_env_v2() is None, reason="v2 integration env vars not configured")
def test_live_v2_openapi_and_operations() -> None:
    live = _live_env_v2()
    assert live is not None
    base_url, auth = live

    glpi = GLPI(base_url=base_url, mode="v2", auth=auth)

    openapi = glpi.v2.load_openapi()
    assert isinstance(openapi, dict)

    operations = glpi.v2.operations()
    assert isinstance(operations, list)

    glpi.close()
