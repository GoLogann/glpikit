"""Changes resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class ChangesResource(GenericItemtypeResource):
    itemtype = "Change"


class AsyncChangesResource(AsyncGenericItemtypeResource):
    itemtype = "Change"
