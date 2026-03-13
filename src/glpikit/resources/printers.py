"""Printers resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class PrintersResource(GenericItemtypeResource):
    itemtype = "Printer"


class AsyncPrintersResource(AsyncGenericItemtypeResource):
    itemtype = "Printer"
