"""Groups resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class GroupsResource(GenericItemtypeResource):
    itemtype = "Group"


class AsyncGroupsResource(AsyncGenericItemtypeResource):
    itemtype = "Group"
