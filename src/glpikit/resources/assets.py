"""Assets resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class AssetsResource(GenericItemtypeResource):
    itemtype = "Asset"


class AsyncAssetsResource(AsyncGenericItemtypeResource):
    itemtype = "Asset"
