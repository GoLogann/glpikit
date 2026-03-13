"""Search DSL wrapper around GLPI search APIs."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any

from glpikit.models import SearchResult

if TYPE_CHECKING:
    from glpikit.async_client import AsyncGLPI
    from glpikit.client import GLPI


class SearchBuilder:
    def __init__(self, client: GLPI, itemtype: str) -> None:
        self.client = client
        self.itemtype = itemtype
        self._criteria: list[dict[str, Any]] = []
        self._sort: int | str | None = None
        self._order: str | None = None
        self._limit: int | None = None
        self._start: int = 0
        self._forcedisplay: list[int | str] | None = None

    def where(self, field: int | str, operator: str, value: Any) -> "SearchBuilder":
        resolved = self.client.items.resolve_search_field(self.itemtype, field)
        self._criteria.append({"field": resolved, "searchtype": operator, "value": value})
        return self

    def and_(self, field: int | str, operator: str, value: Any) -> "SearchBuilder":
        resolved = self.client.items.resolve_search_field(self.itemtype, field)
        self._criteria.append(
            {"link": "AND", "field": resolved, "searchtype": operator, "value": value}
        )
        return self

    def or_(self, field: int | str, operator: str, value: Any) -> "SearchBuilder":
        resolved = self.client.items.resolve_search_field(self.itemtype, field)
        self._criteria.append(
            {"link": "OR", "field": resolved, "searchtype": operator, "value": value}
        )
        return self

    def sort(self, field: int | str, order: str = "asc") -> "SearchBuilder":
        self._sort = self.client.items.resolve_search_field(self.itemtype, field)
        self._order = order.lower()
        return self

    def limit(self, limit: int, *, start: int = 0) -> "SearchBuilder":
        self._limit = limit
        self._start = start
        return self

    def display(self, *fields: int | str) -> "SearchBuilder":
        self._forcedisplay = [self.client.items.resolve_search_field(self.itemtype, f) for f in fields]
        return self

    def run(self) -> SearchResult:
        return self.client.items.search(
            self.itemtype,
            criteria=self._criteria or None,
            range_start=self._start,
            range_limit=self._limit,
            sort=self._sort,
            order=self._order,
            forcedisplay=self._forcedisplay,
        )

    def iter(self, *, page_size: int = 100, max_pages: int | None = None) -> Iterator[dict[str, Any]]:
        yield from self.client.items.iter_search(
            self.itemtype,
            criteria=self._criteria or None,
            sort=self._sort,
            order=self._order,
            forcedisplay=self._forcedisplay,
            page_size=page_size,
            start=self._start,
            max_pages=max_pages,
        )


class AsyncSearchBuilder:
    def __init__(self, client: AsyncGLPI, itemtype: str) -> None:
        self.client = client
        self.itemtype = itemtype
        self._criteria: list[dict[str, Any]] = []
        self._sort: int | str | None = None
        self._order: str | None = None
        self._limit: int | None = None
        self._start: int = 0
        self._forcedisplay: list[int | str] | None = None

    def where(self, field: int | str, operator: str, value: Any) -> "AsyncSearchBuilder":
        self._criteria.append({"field": field, "searchtype": operator, "value": value})
        return self

    def and_(self, field: int | str, operator: str, value: Any) -> "AsyncSearchBuilder":
        self._criteria.append(
            {"link": "AND", "field": field, "searchtype": operator, "value": value}
        )
        return self

    def or_(self, field: int | str, operator: str, value: Any) -> "AsyncSearchBuilder":
        self._criteria.append(
            {"link": "OR", "field": field, "searchtype": operator, "value": value}
        )
        return self

    def sort(self, field: int | str, order: str = "asc") -> "AsyncSearchBuilder":
        self._sort = field
        self._order = order.lower()
        return self

    def limit(self, limit: int, *, start: int = 0) -> "AsyncSearchBuilder":
        self._limit = limit
        self._start = start
        return self

    def display(self, *fields: int | str) -> "AsyncSearchBuilder":
        self._forcedisplay = list(fields)
        return self

    async def run(self) -> SearchResult:
        criteria = await self._resolved_criteria()
        sort = await self._resolved_sort()
        forcedisplay = await self._resolved_forcedisplay()
        return await self.client.items.search(
            self.itemtype,
            criteria=criteria,
            range_start=self._start,
            range_limit=self._limit,
            sort=sort,
            order=self._order,
            forcedisplay=forcedisplay,
        )

    async def iter(
        self,
        *,
        page_size: int = 100,
        max_pages: int | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        async for row in self.aiter(page_size=page_size, max_pages=max_pages):
            rows.append(row)
        return rows

    async def aiter(
        self,
        *,
        page_size: int = 100,
        max_pages: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        criteria = await self._resolved_criteria()
        sort = await self._resolved_sort()
        forcedisplay = await self._resolved_forcedisplay()
        async for row in self.client.items.aiter_search(
            self.itemtype,
            criteria=criteria,
            sort=sort,
            order=self._order,
            forcedisplay=forcedisplay,
            page_size=page_size,
            start=self._start,
            max_pages=max_pages,
        ):
            yield row

    async def _resolved_criteria(self) -> list[dict[str, Any]] | None:
        if not self._criteria:
            return None
        resolved: list[dict[str, Any]] = []
        for criterion in self._criteria:
            current = dict(criterion)
            current["field"] = await self.client.items.resolve_search_field(
                self.itemtype,
                criterion.get("field"),
            )
            resolved.append(current)
        return resolved

    async def _resolved_sort(self) -> int | str | None:
        if self._sort is None:
            return None
        return await self.client.items.resolve_search_field(self.itemtype, self._sort)

    async def _resolved_forcedisplay(self) -> list[int | str] | None:
        if not self._forcedisplay:
            return self._forcedisplay
        values: list[int | str] = []
        for field in self._forcedisplay:
            values.append(await self.client.items.resolve_search_field(self.itemtype, field))
        return values
