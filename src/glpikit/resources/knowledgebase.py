"""Knowledgebase resource wrappers."""

from __future__ import annotations

from ._generic import AsyncGenericItemtypeResource, GenericItemtypeResource


class KnowledgebaseResource(GenericItemtypeResource):
    itemtype = "KnowbaseItem"


class AsyncKnowledgebaseResource(AsyncGenericItemtypeResource):
    itemtype = "KnowbaseItem"
