"""Profiles resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class ProfilesResource(GenericItemtypeResource):
    itemtype = "Profile"


class AsyncProfilesResource(AsyncGenericItemtypeResource):
    itemtype = "Profile"
