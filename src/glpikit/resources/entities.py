"""Entities resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class EntitiesResource(GenericItemtypeResource):
    itemtype = "Entity"


class AsyncEntitiesResource(AsyncGenericItemtypeResource):
    itemtype = "Entity"
