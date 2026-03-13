"""GraphQL read-only client."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from glpikit.models import GraphQLResponse

from .builder import GraphQLQueryBuilder

if TYPE_CHECKING:
    from glpikit.async_client import AsyncGLPI
    from glpikit.client import GLPI

INTROSPECTION_QUERY = """
query IntrospectionQuery {
  __schema {
    queryType { name }
    types { name kind }
  }
}
""".strip()


class GraphQLClient:
    def __init__(self, client: GLPI) -> None:
        self.client = client

    def execute(self, query: str, variables: dict[str, Any] | None = None) -> GraphQLResponse:
        payload = {"query": query, "variables": variables or {}}
        response = self.client._request("POST", self.client._graphql_path(), json=payload)
        return GraphQLResponse.model_validate(response)

    def query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any] | None:
        result = self.execute(query, variables)
        return result.data

    def schema(self) -> GraphQLResponse:
        return self.execute(INTROSPECTION_QUERY)

    def builder(self, root: str) -> GraphQLQueryBuilder:
        return GraphQLQueryBuilder(root)


class AsyncGraphQLClient:
    def __init__(self, client: AsyncGLPI) -> None:
        self.client = client

    async def execute(self, query: str, variables: dict[str, Any] | None = None) -> GraphQLResponse:
        payload = {"query": query, "variables": variables or {}}
        response = await self.client._request("POST", self.client._graphql_path(), json=payload)
        return GraphQLResponse.model_validate(response)

    async def query(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any] | None:
        result = await self.execute(query, variables)
        return result.data

    async def schema(self) -> GraphQLResponse:
        return await self.execute(INTROSPECTION_QUERY)

    def builder(self, root: str) -> GraphQLQueryBuilder:
        return GraphQLQueryBuilder(root)
