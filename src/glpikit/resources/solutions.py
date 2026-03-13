"""Solutions resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class SolutionsResource(GenericItemtypeResource):
    itemtype = "ITILSolution"


class AsyncSolutionsResource(AsyncGenericItemtypeResource):
    itemtype = "ITILSolution"
