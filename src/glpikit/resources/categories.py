"""Categories resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class CategoriesResource(GenericItemtypeResource):
    itemtype = "ITILCategory"


class AsyncCategoriesResource(AsyncGenericItemtypeResource):
    itemtype = "ITILCategory"
