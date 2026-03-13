"""Contracts resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class ContractsResource(GenericItemtypeResource):
    itemtype = "Contract"


class AsyncContractsResource(AsyncGenericItemtypeResource):
    itemtype = "Contract"
