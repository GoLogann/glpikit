"""Computers resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class ComputersResource(GenericItemtypeResource):
    itemtype = "Computer"


class AsyncComputersResource(AsyncGenericItemtypeResource):
    itemtype = "Computer"
