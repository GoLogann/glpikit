"""Problems resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class ProblemsResource(GenericItemtypeResource):
    itemtype = "Problem"


class AsyncProblemsResource(AsyncGenericItemtypeResource):
    itemtype = "Problem"
