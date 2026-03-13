"""Integrations for agent frameworks (MCP, LangChain, LangGraph)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from glpikit.client import GLPI

from .schemas import (
    AddFollowupInput,
    CreateTicketInput,
    GetEntityInput,
    GetTicketInput,
    SearchTicketInput,
    SearchUserInput,
    UpdateTicketInput,
)
from .tools import (
    add_followup_tool,
    create_ticket_tool,
    get_entity_tool,
    get_ticket_tool,
    search_ticket_tool,
    search_user_tool,
    update_ticket_tool,
)


def _tool_catalog(glpi: GLPI) -> dict[str, tuple[Callable[..., Any], type[Any]]]:
    return {
        "create_ticket": (create_ticket_tool(glpi), CreateTicketInput),
        "search_ticket": (search_ticket_tool(glpi), SearchTicketInput),
        "get_ticket": (get_ticket_tool(glpi), GetTicketInput),
        "update_ticket": (update_ticket_tool(glpi), UpdateTicketInput),
        "add_followup": (add_followup_tool(glpi), AddFollowupInput),
        "search_user": (search_user_tool(glpi), SearchUserInput),
        "get_entity": (get_entity_tool(glpi), GetEntityInput),
    }


def as_mcp_tools(glpi: GLPI) -> list[dict[str, Any]]:
    tools = []
    for name, (_callable, schema) in _tool_catalog(glpi).items():
        tools.append(
            {
                "name": name,
                "description": f"GLPI tool: {name}",
                "input_schema": schema.model_json_schema(),
            }
        )
    return tools


def as_langgraph_nodes(glpi: GLPI) -> dict[str, Callable[..., Any]]:
    return {name: fn for name, (fn, _schema) in _tool_catalog(glpi).items()}


def as_langchain_tools(glpi: GLPI) -> list[Any]:
    catalog = _tool_catalog(glpi)
    try:
        from langchain_core.tools import StructuredTool  # type: ignore
    except Exception:
        return [
            {
                "name": name,
                "callable": fn,
                "schema": schema.model_json_schema(),
            }
            for name, (fn, schema) in catalog.items()
        ]

    tools = []
    for name, (fn, schema) in catalog.items():
        tools.append(
            StructuredTool.from_function(
                name=name,
                description=f"GLPI tool: {name}",
                func=fn,
                args_schema=schema,
            )
        )
    return tools
