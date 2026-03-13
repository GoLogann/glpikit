"""Followups resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class FollowupsResource(GenericItemtypeResource):
    itemtype = "ITILFollowup"


class AsyncFollowupsResource(AsyncGenericItemtypeResource):
    itemtype = "ITILFollowup"
