"""Command-line interface for glpikit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from glpikit import GLPI


def _parse_scalar(raw: str) -> Any:
    normalized = raw.strip()
    lowered = normalized.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "none"}:
        return None

    if normalized.startswith("{") or normalized.startswith("["):
        try:
            return json.loads(normalized)
        except ValueError:
            return raw

    try:
        return int(normalized)
    except ValueError:
        pass

    try:
        return float(normalized)
    except ValueError:
        return raw


def _parse_pairs(values: list[str] | None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for value in values or []:
        if "=" not in value:
            continue
        key, raw = value.split("=", maxsplit=1)
        parsed = _parse_scalar(raw)
        if key in payload:
            current = payload[key]
            if isinstance(current, list):
                current.append(parsed)
            else:
                payload[key] = [current, parsed]
        else:
            payload[key] = parsed
    return payload


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True, by_alias=True)
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    return value


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="glpikit")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("capabilities")

    tickets = sub.add_parser("tickets-get")
    tickets.add_argument("ticket_id", type=int)

    search = sub.add_parser("search")
    search.add_argument("itemtype")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=10)

    v2_call = sub.add_parser("v2-call")
    v2_call.add_argument("operation_id")
    v2_call.add_argument("--param", action="append")
    v2_call.add_argument("--json")

    v2_ops = sub.add_parser("v2-operations")
    v2_ops.add_argument("--refresh", action="store_true")

    upload = sub.add_parser("documents-upload")
    upload.add_argument("file_path")
    upload.add_argument("--name")
    upload.add_argument("--entity-id", type=int)

    download = sub.add_parser("documents-download")
    download.add_argument("document_id", type=int)
    download.add_argument("--to", required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    glpi = GLPI.from_env()
    output: Any

    if args.command == "capabilities":
        output = glpi.capabilities()
    elif args.command == "tickets-get":
        output = glpi.tickets.get(args.ticket_id)
    elif args.command == "search":
        output = glpi.search(args.itemtype).where("name", "contains", args.query).limit(args.limit).run()
    elif args.command == "v2-call":
        params = _parse_pairs(args.param)
        if args.json:
            params["json"] = json.loads(args.json)
        output = glpi.v2.call(args.operation_id, **params)
    elif args.command == "v2-operations":
        if args.refresh:
            glpi.v2.load_openapi(force_refresh=True)
        output = glpi.v2.operations()
    elif args.command == "documents-upload":
        output = glpi.documents.upload(
            file_path=args.file_path,
            name=args.name,
            entity_id=args.entity_id,
        )
    elif args.command == "documents-download":
        destination = Path(args.to)
        output = {
            "bytes": len(glpi.documents.download(args.document_id, to=str(destination))),
            "path": str(destination),
        }
    else:  # pragma: no cover - argparse guards this
        parser.print_help()
        return 1

    print(json.dumps(_to_jsonable(output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
