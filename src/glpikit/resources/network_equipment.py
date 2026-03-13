"""NetworkEquipment resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class NetworkEquipmentResource(GenericItemtypeResource):
    itemtype = "NetworkEquipment"


class AsyncNetworkEquipmentResource(AsyncGenericItemtypeResource):
    itemtype = "NetworkEquipment"
