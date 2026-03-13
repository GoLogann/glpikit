"""AI tool helpers to expose SDK operations as callables."""

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


def create_ticket_tool(glpi: GLPI) -> Callable[..., Any]:
    def tool(**kwargs: Any) -> Any:
        data = CreateTicketInput.model_validate(kwargs)
        return glpi.tickets.create(**data.model_dump(exclude_none=True))

    return tool


def search_ticket_tool(glpi: GLPI) -> Callable[..., Any]:
    def tool(**kwargs: Any) -> Any:
        data = SearchTicketInput.model_validate(kwargs)
        return glpi.search("Ticket").where("name", "contains", data.query).limit(data.limit).run()

    return tool


def add_followup_tool(glpi: GLPI) -> Callable[..., Any]:
    def tool(**kwargs: Any) -> Any:
        data = AddFollowupInput.model_validate(kwargs)
        return glpi.tickets.add_followup(data.ticket_id, data.content)

    return tool


def get_ticket_tool(glpi: GLPI) -> Callable[..., Any]:
    def tool(**kwargs: Any) -> Any:
        data = GetTicketInput.model_validate(kwargs)
        return glpi.tickets.get(data.ticket_id)

    return tool


def update_ticket_tool(glpi: GLPI) -> Callable[..., Any]:
    def tool(**kwargs: Any) -> Any:
        data = UpdateTicketInput.model_validate(kwargs)
        payload = data.model_dump(exclude_none=True)
        ticket_id = payload.pop("ticket_id")
        return glpi.tickets.update(ticket_id, **payload)

    return tool


def search_user_tool(glpi: GLPI) -> Callable[..., Any]:
    def tool(**kwargs: Any) -> Any:
        data = SearchUserInput.model_validate(kwargs)
        return glpi.search("User").where("name", "contains", data.query).limit(data.limit).run()

    return tool


def get_entity_tool(glpi: GLPI) -> Callable[..., Any]:
    def tool(**kwargs: Any) -> Any:
        data = GetEntityInput.model_validate(kwargs)
        return glpi.entities.get(data.entity_id)

    return tool
