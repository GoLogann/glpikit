"""Ticket domain resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from glpikit.models import Followup, Ticket

from .base import AsyncResourceBase, ResourceBase

if TYPE_CHECKING:
    from glpikit.async_client import AsyncGLPI
    from glpikit.client import GLPI


def _ticket_payload(
    *,
    title: str | None = None,
    description: str | None = None,
    category_id: int | None = None,
    requester_email: str | None = None,
    urgency: int | None = None,
    impact: int | None = None,
    priority: int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    payload = dict(extra)
    if title is not None:
        payload["name"] = title
    if description is not None:
        payload["content"] = description
    if category_id is not None:
        payload["itilcategories_id"] = category_id
    if requester_email is not None:
        payload["_users_id_requester_email"] = requester_email
    if urgency is not None:
        payload["urgency"] = urgency
    if impact is not None:
        payload["impact"] = impact
    if priority is not None:
        payload["priority"] = priority
    return payload


class TicketFollowupsResource(ResourceBase):
    def list(self, ticket_id: int) -> list[Followup]:
        path = self.client._subitem_path("Ticket", ticket_id, "ITILFollowup")
        payload = self._request("GET", path)
        if not isinstance(payload, list):
            payload = [payload]
        return [Followup.model_validate(entry) for entry in payload]

    def create(self, ticket_id: int, content: str, **extra: Any) -> Followup:
        payload = {"tickets_id": ticket_id, "content": content, **extra}
        response = self.client.items.create("ITILFollowup", payload)
        return Followup.model_validate(response)


class AsyncTicketFollowupsResource(AsyncResourceBase):
    async def list(self, ticket_id: int) -> list[Followup]:
        path = self.client._subitem_path("Ticket", ticket_id, "ITILFollowup")
        payload = await self._request("GET", path)
        if not isinstance(payload, list):
            payload = [payload]
        return [Followup.model_validate(entry) for entry in payload]

    async def create(self, ticket_id: int, content: str, **extra: Any) -> Followup:
        payload = {"tickets_id": ticket_id, "content": content, **extra}
        created = await self.client.items.create("ITILFollowup", payload)
        return Followup.model_validate(created)


class TicketsResource(ResourceBase):
    def __init__(self, client: GLPI) -> None:
        super().__init__(client)
        self.followups = TicketFollowupsResource(client)

    def create(
        self,
        *,
        title: str,
        description: str,
        category_id: int | None = None,
        requester_email: str | None = None,
        urgency: int | None = None,
        impact: int | None = None,
        priority: int | None = None,
        **extra: Any,
    ) -> Ticket:
        payload = _ticket_payload(
            title=title,
            description=description,
            category_id=category_id,
            requester_email=requester_email,
            urgency=urgency,
            impact=impact,
            priority=priority,
            **extra,
        )
        created = self.client.items.create("Ticket", payload)
        return Ticket.model_validate(created)

    def get(self, ticket_id: int, *, params: dict[str, Any] | None = None) -> Ticket:
        payload = self.client.items.get("Ticket", ticket_id, params=params)
        return Ticket.model_validate(payload)

    def update(self, ticket_id: int, **fields: Any) -> Ticket:
        payload = _ticket_payload(**fields)
        updated = self.client.items.update("Ticket", ticket_id, payload)
        return Ticket.model_validate(updated)

    def search(self, **kwargs: Any) -> Any:
        return self.client.items.search("Ticket", **kwargs)

    def add_followup(self, ticket_id: int, content: str, **extra: Any) -> Followup:
        return self.followups.create(ticket_id, content, **extra)

    def assign(
        self,
        ticket_id: int,
        *,
        user_id: int | None = None,
        group_id: int | None = None,
    ) -> Ticket:
        if user_id is None and group_id is None:
            raise ValueError("assign requires user_id or group_id")
        payload: dict[str, Any] = {}
        if user_id is not None:
            payload["users_id_assign"] = user_id
        if group_id is not None:
            payload["groups_id_assign"] = group_id
        return self.update(ticket_id, **payload)

    def add_solution(self, ticket_id: int, content: str, *, status: int | None = None) -> Any:
        payload: dict[str, Any] = {
            "tickets_id": ticket_id,
            "content": content,
        }
        if status is not None:
            payload["status"] = status
        return self.client.items.create("ITILSolution", payload)


class AsyncTicketsResource(AsyncResourceBase):
    def __init__(self, client: AsyncGLPI) -> None:
        super().__init__(client)
        self.followups = AsyncTicketFollowupsResource(client)

    async def create(
        self,
        *,
        title: str,
        description: str,
        category_id: int | None = None,
        requester_email: str | None = None,
        urgency: int | None = None,
        impact: int | None = None,
        priority: int | None = None,
        **extra: Any,
    ) -> Ticket:
        payload = _ticket_payload(
            title=title,
            description=description,
            category_id=category_id,
            requester_email=requester_email,
            urgency=urgency,
            impact=impact,
            priority=priority,
            **extra,
        )
        created = await self.client.items.create("Ticket", payload)
        return Ticket.model_validate(created)

    async def get(self, ticket_id: int, *, params: dict[str, Any] | None = None) -> Ticket:
        payload = await self.client.items.get("Ticket", ticket_id, params=params)
        return Ticket.model_validate(payload)

    async def update(self, ticket_id: int, **fields: Any) -> Ticket:
        payload = _ticket_payload(**fields)
        updated = await self.client.items.update("Ticket", ticket_id, payload)
        return Ticket.model_validate(updated)

    async def search(self, **kwargs: Any) -> Any:
        return await self.client.items.search("Ticket", **kwargs)

    async def add_followup(self, ticket_id: int, content: str, **extra: Any) -> Followup:
        payload = {"tickets_id": ticket_id, "content": content, **extra}
        created = await self.client.items.create("ITILFollowup", payload)
        return Followup.model_validate(created)

    async def assign(
        self,
        ticket_id: int,
        *,
        user_id: int | None = None,
        group_id: int | None = None,
    ) -> Ticket:
        if user_id is None and group_id is None:
            raise ValueError("assign requires user_id or group_id")
        payload: dict[str, Any] = {}
        if user_id is not None:
            payload["users_id_assign"] = user_id
        if group_id is not None:
            payload["groups_id_assign"] = group_id
        return await self.update(ticket_id, **payload)

    async def add_solution(self, ticket_id: int, content: str, *, status: int | None = None) -> Any:
        payload: dict[str, Any] = {
            "tickets_id": ticket_id,
            "content": content,
        }
        if status is not None:
            payload["status"] = status
        return await self.client.items.create("ITILSolution", payload)
