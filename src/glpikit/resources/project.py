"""Project resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class ProjectResource(GenericItemtypeResource):
    itemtype = "Project"


class AsyncProjectResource(AsyncGenericItemtypeResource):
    itemtype = "Project"
