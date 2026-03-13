"""Small helper to compose GraphQL read-only queries."""

from __future__ import annotations


class GraphQLQueryBuilder:
    def __init__(self, root: str) -> None:
        self.root = root
        self._fields: list[str] = []
        self._args: dict[str, str] = {}

    def arg(self, name: str, value_expr: str) -> "GraphQLQueryBuilder":
        self._args[name] = value_expr
        return self

    def field(self, field_name: str) -> "GraphQLQueryBuilder":
        self._fields.append(field_name)
        return self

    def build(self) -> str:
        args = ""
        if self._args:
            args = "(" + ", ".join(f"{k}: {v}" for k, v in self._args.items()) + ")"
        fields = " ".join(self._fields) if self._fields else "id"
        return f"query {{ {self.root}{args} {{ {fields} }} }}"
