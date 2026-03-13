"""Tasks resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class TasksResource(GenericItemtypeResource):
    itemtype = "TicketTask"


class AsyncTasksResource(AsyncGenericItemtypeResource):
    itemtype = "TicketTask"
