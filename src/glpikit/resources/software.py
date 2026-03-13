"""Software resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class SoftwareResource(GenericItemtypeResource):
    itemtype = "Software"


class AsyncSoftwareResource(AsyncGenericItemtypeResource):
    itemtype = "Software"
