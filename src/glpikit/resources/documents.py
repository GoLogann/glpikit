"""Document resource with upload/download helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, BinaryIO

from glpikit.models import Document

from .base import AsyncResourceBase, ResourceBase


class DocumentsResource(ResourceBase):
    def upload(
        self,
        *,
        file_path: str | None = None,
        file_bytes: bytes | None = None,
        file_obj: BinaryIO | None = None,
        filename: str | None = None,
        name: str | None = None,
        entity_id: int | None = None,
        **extra: Any,
    ) -> Document:
        if sum(v is not None for v in (file_path, file_bytes, file_obj)) != 1:
            raise ValueError("provide exactly one of file_path, file_bytes or file_obj")

        if file_path is not None:
            p = Path(file_path)
            stream = p.open("rb")
            close_stream = True
            upload_name = filename or p.name
        elif file_bytes is not None:
            upload_name = filename or "upload.bin"
            stream = file_bytes
            close_stream = False
        else:
            upload_name = filename or "upload.bin"
            stream = file_obj
            close_stream = False

        payload = {
            "name": name or upload_name,
            "entities_id": entity_id,
            **extra,
        }

        try:
            files = {
                "uploadManifest": (None, self.client._to_upload_manifest(payload), "application/json"),
                "filename[0]": (upload_name, stream, "application/octet-stream"),
            }
            response = self.client._request("POST", self.client._document_upload_path(), files=files)
            return Document.model_validate(response)
        finally:
            if close_stream:
                stream.close()  # type: ignore[attr-defined]

    def download(self, document_id: int, *, to: str | None = None) -> bytes:
        path = self.client._document_download_path(document_id)
        data = self.client._request("GET", path, headers={"Accept": "application/octet-stream"})
        if isinstance(data, str):
            content = data.encode("utf-8")
        elif isinstance(data, bytes):
            content = data
        else:
            content = bytes(str(data), "utf-8")

        if to:
            Path(to).write_bytes(content)
        return content

    def get(self, document_id: int) -> Document:
        payload = self.client.items.get("Document", document_id)
        return Document.model_validate(payload)


class AsyncDocumentsResource(AsyncResourceBase):
    async def upload(
        self,
        *,
        file_path: str | None = None,
        file_bytes: bytes | None = None,
        file_obj: BinaryIO | None = None,
        filename: str | None = None,
        name: str | None = None,
        entity_id: int | None = None,
        **extra: Any,
    ) -> Document:
        if sum(v is not None for v in (file_path, file_bytes, file_obj)) != 1:
            raise ValueError("provide exactly one of file_path, file_bytes or file_obj")

        if file_path is not None:
            p = Path(file_path)
            stream = p.open("rb")
            close_stream = True
            upload_name = filename or p.name
        elif file_bytes is not None:
            upload_name = filename or "upload.bin"
            stream = file_bytes
            close_stream = False
        else:
            upload_name = filename or "upload.bin"
            stream = file_obj
            close_stream = False

        payload = {
            "name": name or upload_name,
            "entities_id": entity_id,
            **extra,
        }

        try:
            files = {
                "uploadManifest": (None, self.client._to_upload_manifest(payload), "application/json"),
                "filename[0]": (upload_name, stream, "application/octet-stream"),
            }
            response = await self.client._request("POST", self.client._document_upload_path(), files=files)
            return Document.model_validate(response)
        finally:
            if close_stream:
                stream.close()  # type: ignore[attr-defined]

    async def download(self, document_id: int, *, to: str | None = None) -> bytes:
        path = self.client._document_download_path(document_id)
        data = await self.client._request("GET", path, headers={"Accept": "application/octet-stream"})
        if isinstance(data, str):
            content = data.encode("utf-8")
        elif isinstance(data, bytes):
            content = data
        else:
            content = bytes(str(data), "utf-8")

        if to:
            Path(to).write_bytes(content)
        return content

    async def get(self, document_id: int) -> Document:
        payload = await self.client.items.get("Document", document_id)
        return Document.model_validate(payload)
