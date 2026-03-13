"""Locations resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class LocationsResource(GenericItemtypeResource):
    itemtype = "Location"


class AsyncLocationsResource(AsyncGenericItemtypeResource):
    itemtype = "Location"
