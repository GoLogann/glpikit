from __future__ import annotations

import json

from glpikit.ai.integrations import as_langchain_tools, as_langgraph_nodes, as_mcp_tools
from glpikit.cli import main


class _FakeTickets:
    def get(self, ticket_id: int):
        return {"id": ticket_id}


class _FakeDocuments:
    def upload(self, **kwargs):
        return {"id": 1, **kwargs}

    def download(self, document_id: int, *, to: str | None = None):
        return b"abc"


class _FakeV2:
    def call(self, operation_id: str, **kwargs):
        return {"operation_id": operation_id, "kwargs": kwargs}

    def operations(self):
        return ["getTicket", "createTicket"]

    def load_openapi(self, *, force_refresh: bool = False):
        return {"refreshed": force_refresh}


class _FakeSearch:
    def where(self, _field, _operator, query):
        self._query = query
        return self

    def limit(self, value):
        self._limit = value
        return self

    def run(self):
        return {"query": self._query, "limit": self._limit}


class _FakeEntities:
    def get(self, entity_id: int):
        return {"id": entity_id}


class _FakeGLPI:
    def __init__(self):
        self.tickets = _FakeTickets()
        self.documents = _FakeDocuments()
        self.v2 = _FakeV2()
        self.entities = _FakeEntities()

    @classmethod
    def from_env(cls):
        return cls()

    def capabilities(self):
        return {"mode": "v1"}

    def search(self, _itemtype):
        return _FakeSearch()


def test_cli_commands(monkeypatch, capsys):
    monkeypatch.setattr("glpikit.cli.GLPI", _FakeGLPI)

    assert main(["capabilities"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["mode"] == "v1"

    assert main(["tickets-get", "9"]) == 0
    out = capsys.readouterr().out
    assert json.loads(out)["id"] == 9

    assert main(["v2-call", "getTicket", "--param", "id=5", "--param", "active=true"]) == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed["operation_id"] == "getTicket"
    assert parsed["kwargs"]["id"] == 5
    assert parsed["kwargs"]["active"] is True

    assert main(["v2-operations"]) == 0
    out = capsys.readouterr().out
    assert "getTicket" in json.loads(out)


def test_agent_integrations():
    fake = _FakeGLPI()

    mcp = as_mcp_tools(fake)
    assert any(tool["name"] == "create_ticket" for tool in mcp)

    nodes = as_langgraph_nodes(fake)
    assert "get_ticket" in nodes

    tools = as_langchain_tools(fake)
    assert len(tools) >= 3
