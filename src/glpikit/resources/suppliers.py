"""Suppliers resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class SuppliersResource(GenericItemtypeResource):
    itemtype = "Supplier"


class AsyncSuppliersResource(AsyncGenericItemtypeResource):
    itemtype = "Supplier"
