"""Appliances resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class AppliancesResource(GenericItemtypeResource):
    itemtype = "Appliance"


class AsyncAppliancesResource(AsyncGenericItemtypeResource):
    itemtype = "Appliance"
