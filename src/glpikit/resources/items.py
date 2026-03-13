"""Generic CRUD, iterators and search operations."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterable, Iterator, Sequence
from typing import Any

from glpikit.models import BulkReport, SearchResult
from glpikit.utils import chunked, process_bulk, process_bulk_async

from .base import AsyncResourceBase, ResourceBase


def _normalize_create_payload(mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    if mode != "v1":
        return payload
    if "input" in payload:
        return payload
    return {"input": payload}


def _normalize_update_payload(mode: str, item_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    if mode != "v1":
        return payload
    if "input" in payload:
        return payload
    merged = {"id": item_id, **payload}
    return {"input": merged}


def _build_range(start: int, limit: int | None) -> str:
    if limit is None:
        return f"{start}-{start}"
    end = start + max(0, limit) - 1
    return f"{start}-{end}"


def _search_cache_key(itemtype: str) -> str:
    return f"search_options::{itemtype.lower()}"


def _extract_search_options_map(raw: Any) -> dict[str, int | str]:
    mapping: dict[str, int | str] = {}
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        items = enumerate(raw)
    else:
        return mapping

    for key, value in items:
        if isinstance(value, dict):
            field_id = value.get("id", key)
            uid = value.get("uid")
            name = value.get("name")
            if uid and isinstance(uid, str):
                mapping[uid.lower()] = field_id
            if name and isinstance(name, str):
                mapping[name.lower()] = field_id
            if isinstance(field_id, str):
                mapping[field_id.lower()] = field_id
        elif isinstance(key, str):
            mapping[key.lower()] = key
    return mapping


class ItemsResource(ResourceBase):
    def get(self, itemtype: str, item_id: int, *, params: dict[str, Any] | None = None) -> Any:
        path = self.client._item_path(itemtype, item_id)
        payload = self._request("GET", path, params=params)
        return self.client._coerce_item(itemtype, payload)

    def list(self, itemtype: str, *, params: dict[str, Any] | None = None) -> Sequence[Any]:
        path = self.client._item_collection_path(itemtype)
        payload = self._request("GET", path, params=params)
        if isinstance(payload, list):
            return [self.client._coerce_item(itemtype, entry) for entry in payload]
        return [self.client._coerce_item(itemtype, payload)]

    def iter_all(
        self,
        itemtype: str,
        *,
        page_size: int = 100,
        start: int = 0,
        params: dict[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> Iterator[Any]:
        cursor = start
        page = 0
        while True:
            page += 1
            if max_pages is not None and page > max_pages:
                return

            page_params = dict(params or {})
            page_params.setdefault("range", _build_range(cursor, page_size))
            records = list(self.list(itemtype, params=page_params))
            if not records:
                return

            for record in records:
                yield record

            if len(records) < page_size:
                return
            cursor += page_size

    def create(self, itemtype: str, payload: dict[str, Any]) -> Any:
        path = self.client._item_collection_path(itemtype)
        body = _normalize_create_payload(self.client.mode, payload)
        response = self._request("POST", path, json=body)
        return self.client._coerce_item(itemtype, response)

    def update(self, itemtype: str, item_id: int, payload: dict[str, Any]) -> Any:
        path = self.client._item_path(itemtype, item_id)
        body = _normalize_update_payload(self.client.mode, item_id, payload)
        response = self._request("PUT", path, json=body)
        return self.client._coerce_item(itemtype, response)

    def delete(
        self,
        itemtype: str,
        item_id: int,
        *,
        force_purge: bool = False,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        path = self.client._item_path(itemtype, item_id)
        params = {"force_purge": 1} if force_purge else None
        return self._request("DELETE", path, params=params, confirmed=confirmed, dry_run=dry_run)

    def bulk_create(
        self,
        itemtype: str,
        payloads: Iterable[dict[str, Any]],
        *,
        chunk_size: int = 100,
        retries: int = 1,
    ) -> BulkReport:
        report_items: list[BulkReport] = []
        final_items = []
        for batch in chunked(payloads, chunk_size):
            report = process_bulk(batch, lambda payload: self.create(itemtype, payload), retries=retries)
            report_items.append(report)
            final_items.extend(report.items)

        succeeded = sum(1 for entry in final_items if entry.success)
        failed = len(final_items) - succeeded
        return BulkReport(total=len(final_items), succeeded=succeeded, failed=failed, items=final_items)

    def bulk_update(
        self,
        itemtype: str,
        payloads: Iterable[dict[str, Any]],
        *,
        id_field: str = "id",
        chunk_size: int = 100,
        retries: int = 1,
    ) -> BulkReport:
        final_items = []
        for batch in chunked(payloads, chunk_size):
            report = process_bulk(
                batch,
                lambda payload: self.update(itemtype, int(payload[id_field]), payload),
                retries=retries,
            )
            final_items.extend(report.items)

        succeeded = sum(1 for entry in final_items if entry.success)
        failed = len(final_items) - succeeded
        return BulkReport(total=len(final_items), succeeded=succeeded, failed=failed, items=final_items)

    def bulk_delete(
        self,
        itemtype: str,
        ids: Iterable[int],
        *,
        chunk_size: int = 100,
        retries: int = 1,
    ) -> BulkReport:
        final_items = []
        for batch in chunked(ids, chunk_size):
            report = process_bulk(
                batch,
                lambda item_id: self.delete(itemtype, int(item_id), confirmed=True),
                retries=retries,
            )
            final_items.extend(report.items)

        succeeded = sum(1 for entry in final_items if entry.success)
        failed = len(final_items) - succeeded
        return BulkReport(total=len(final_items), succeeded=succeeded, failed=failed, items=final_items)

    def get_multiple(self, items: list[dict[str, Any]]) -> Any:
        if self.client.mode != "v1":
            raise NotImplementedError("getMultipleItems is only mapped for v1")
        return self._request("GET", "/apirest.php/getMultipleItems", params={"items": items})

    def list_search_options(self, itemtype: str, *, refresh: bool = False) -> Any:
        cache_key = _search_cache_key(itemtype)
        if not refresh:
            cached = self.client._search_options_cache.get(cache_key)
            if cached is not None:
                return cached

        path = self.client._search_options_path(itemtype)
        payload = self._request("GET", path)
        self.client._search_options_cache.set(cache_key, payload)
        return payload

    def resolve_search_field(self, itemtype: str, field: Any) -> int | str:
        if isinstance(field, int):
            return field
        if not isinstance(field, str):
            return str(field)
        try:
            raw = self.list_search_options(itemtype)
            mapping = _extract_search_options_map(raw)
            return mapping.get(field.lower(), field)
        except Exception:
            return field

    def search(
        self,
        itemtype: str,
        *,
        criteria: list[dict[str, Any]] | None = None,
        range_start: int | None = None,
        range_limit: int | None = None,
        sort: int | str | None = None,
        order: str | None = None,
        forcedisplay: list[int | str] | None = None,
    ) -> SearchResult:
        path = self.client._search_path(itemtype)
        params: dict[str, Any] = {}
        if criteria:
            params["criteria"] = criteria
        if range_start is not None:
            params["range"] = _build_range(range_start, range_limit)
        if sort is not None:
            params["sort"] = sort
        if order is not None:
            params["order"] = order
        if forcedisplay:
            params["forcedisplay"] = forcedisplay
        payload = self._request("GET", path, params=params)
        return SearchResult.model_validate(payload)

    def iter_search(
        self,
        itemtype: str,
        *,
        criteria: list[dict[str, Any]] | None = None,
        sort: int | str | None = None,
        order: str | None = None,
        forcedisplay: list[int | str] | None = None,
        page_size: int = 100,
        start: int = 0,
        max_pages: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        cursor = start
        page = 0
        while True:
            page += 1
            if max_pages is not None and page > max_pages:
                return
            result = self.search(
                itemtype,
                criteria=criteria,
                range_start=cursor,
                range_limit=page_size,
                sort=sort,
                order=order,
                forcedisplay=forcedisplay,
            )
            rows = result.data
            if not rows:
                return
            for row in rows:
                yield row
            if len(rows) < page_size:
                return
            cursor += page_size


class AsyncItemsResource(AsyncResourceBase):
    async def get(self, itemtype: str, item_id: int, *, params: dict[str, Any] | None = None) -> Any:
        path = self.client._item_path(itemtype, item_id)
        payload = await self._request("GET", path, params=params)
        return self.client._coerce_item(itemtype, payload)

    async def list(self, itemtype: str, *, params: dict[str, Any] | None = None) -> Sequence[Any]:
        path = self.client._item_collection_path(itemtype)
        payload = await self._request("GET", path, params=params)
        if isinstance(payload, list):
            return [self.client._coerce_item(itemtype, entry) for entry in payload]
        return [self.client._coerce_item(itemtype, payload)]

    async def iter_all(
        self,
        itemtype: str,
        *,
        page_size: int = 100,
        start: int = 0,
        params: dict[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> list[Any]:
        collected: list[Any] = []
        async for record in self.aiter_all(
            itemtype,
            page_size=page_size,
            start=start,
            params=params,
            max_pages=max_pages,
        ):
            collected.append(record)
        return collected

    async def aiter_all(
        self,
        itemtype: str,
        *,
        page_size: int = 100,
        start: int = 0,
        params: dict[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> AsyncIterator[Any]:
        cursor = start
        page = 0
        while True:
            page += 1
            if max_pages is not None and page > max_pages:
                return

            page_params = dict(params or {})
            page_params.setdefault("range", _build_range(cursor, page_size))
            records = list(await self.list(itemtype, params=page_params))
            if not records:
                return
            for record in records:
                yield record
            if len(records) < page_size:
                return
            cursor += page_size

    async def create(self, itemtype: str, payload: dict[str, Any]) -> Any:
        path = self.client._item_collection_path(itemtype)
        body = _normalize_create_payload(self.client.mode, payload)
        response = await self._request("POST", path, json=body)
        return self.client._coerce_item(itemtype, response)

    async def update(self, itemtype: str, item_id: int, payload: dict[str, Any]) -> Any:
        path = self.client._item_path(itemtype, item_id)
        body = _normalize_update_payload(self.client.mode, item_id, payload)
        response = await self._request("PUT", path, json=body)
        return self.client._coerce_item(itemtype, response)

    async def delete(
        self,
        itemtype: str,
        item_id: int,
        *,
        force_purge: bool = False,
        confirmed: bool = False,
        dry_run: bool | None = None,
    ) -> Any:
        path = self.client._item_path(itemtype, item_id)
        params = {"force_purge": 1} if force_purge else None
        return await self._request(
            "DELETE",
            path,
            params=params,
            confirmed=confirmed,
            dry_run=dry_run,
        )

    async def bulk_create(
        self,
        itemtype: str,
        payloads: Iterable[dict[str, Any]],
        *,
        chunk_size: int = 100,
        retries: int = 1,
    ) -> BulkReport:
        final_items = []
        for batch in chunked(payloads, chunk_size):
            report = await process_bulk_async(
                batch,
                lambda payload: self.create(itemtype, payload),
                retries=retries,
            )
            final_items.extend(report.items)

        succeeded = sum(1 for entry in final_items if entry.success)
        failed = len(final_items) - succeeded
        return BulkReport(total=len(final_items), succeeded=succeeded, failed=failed, items=final_items)

    async def bulk_update(
        self,
        itemtype: str,
        payloads: Iterable[dict[str, Any]],
        *,
        id_field: str = "id",
        chunk_size: int = 100,
        retries: int = 1,
    ) -> BulkReport:
        final_items = []
        for batch in chunked(payloads, chunk_size):
            report = await process_bulk_async(
                batch,
                lambda payload: self.update(itemtype, int(payload[id_field]), payload),
                retries=retries,
            )
            final_items.extend(report.items)

        succeeded = sum(1 for entry in final_items if entry.success)
        failed = len(final_items) - succeeded
        return BulkReport(total=len(final_items), succeeded=succeeded, failed=failed, items=final_items)

    async def bulk_delete(
        self,
        itemtype: str,
        ids: Iterable[int],
        *,
        chunk_size: int = 100,
        retries: int = 1,
    ) -> BulkReport:
        final_items = []
        for batch in chunked(ids, chunk_size):
            report = await process_bulk_async(
                batch,
                lambda item_id: self.delete(itemtype, int(item_id), confirmed=True),
                retries=retries,
            )
            final_items.extend(report.items)

        succeeded = sum(1 for entry in final_items if entry.success)
        failed = len(final_items) - succeeded
        return BulkReport(total=len(final_items), succeeded=succeeded, failed=failed, items=final_items)

    async def get_multiple(self, items: list[dict[str, Any]]) -> Any:
        if self.client.mode != "v1":
            raise NotImplementedError("getMultipleItems is only mapped for v1")
        return await self._request("GET", "/apirest.php/getMultipleItems", params={"items": items})

    async def list_search_options(self, itemtype: str, *, refresh: bool = False) -> Any:
        cache_key = _search_cache_key(itemtype)
        if not refresh:
            cached = self.client._search_options_cache.get(cache_key)
            if cached is not None:
                return cached

        path = self.client._search_options_path(itemtype)
        payload = await self._request("GET", path)
        self.client._search_options_cache.set(cache_key, payload)
        return payload

    async def resolve_search_field(self, itemtype: str, field: Any) -> int | str:
        if isinstance(field, int):
            return field
        if not isinstance(field, str):
            return str(field)
        try:
            raw = await self.list_search_options(itemtype)
            mapping = _extract_search_options_map(raw)
            return mapping.get(field.lower(), field)
        except Exception:
            return field

    async def search(
        self,
        itemtype: str,
        *,
        criteria: list[dict[str, Any]] | None = None,
        range_start: int | None = None,
        range_limit: int | None = None,
        sort: int | str | None = None,
        order: str | None = None,
        forcedisplay: list[int | str] | None = None,
    ) -> SearchResult:
        path = self.client._search_path(itemtype)
        params: dict[str, Any] = {}
        if criteria:
            params["criteria"] = criteria
        if range_start is not None:
            params["range"] = _build_range(range_start, range_limit)
        if sort is not None:
            params["sort"] = sort
        if order is not None:
            params["order"] = order
        if forcedisplay:
            params["forcedisplay"] = forcedisplay
        payload = await self._request("GET", path, params=params)
        return SearchResult.model_validate(payload)

    async def iter_search(
        self,
        itemtype: str,
        *,
        criteria: list[dict[str, Any]] | None = None,
        sort: int | str | None = None,
        order: str | None = None,
        forcedisplay: list[int | str] | None = None,
        page_size: int = 100,
        start: int = 0,
        max_pages: int | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        async for row in self.aiter_search(
            itemtype,
            criteria=criteria,
            sort=sort,
            order=order,
            forcedisplay=forcedisplay,
            page_size=page_size,
            start=start,
            max_pages=max_pages,
        ):
            rows.append(row)
        return rows

    async def aiter_search(
        self,
        itemtype: str,
        *,
        criteria: list[dict[str, Any]] | None = None,
        sort: int | str | None = None,
        order: str | None = None,
        forcedisplay: list[int | str] | None = None,
        page_size: int = 100,
        start: int = 0,
        max_pages: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        cursor = start
        page = 0
        while True:
            page += 1
            if max_pages is not None and page > max_pages:
                return
            result = await self.search(
                itemtype,
                criteria=criteria,
                range_start=cursor,
                range_limit=page_size,
                sort=sort,
                order=order,
                forcedisplay=forcedisplay,
            )
            data = result.data
            if not data:
                return
            for row in data:
                yield row
            if len(data) < page_size:
                return
            cursor += page_size
