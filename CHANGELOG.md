# Changelog

## Unreleased

- added TTL cache for `searchOptions`
- added iterators and bulk operations (`iter_all`, `iter_search`, `bulk_create/update/delete`)
- added policy engine and dry-run support for destructive actions
- added OAuth2 PKCE helpers and authorization-code token exchange support
- added OpenAPI typed operation parsing via `v2.call_typed(...)`
- added CLI entrypoint (`glpikit`)
- added agent integration helpers for MCP/LangChain/LangGraph
- added observability metrics collector and optional OpenTelemetry hooks
- added live integration test scaffolding (Docker compose + matrix helper + CI workflow)

## 0.1.0 - 2026-03-13

- SDK base sync/async para GLPI v1/v2/GraphQL
- auth v1 (session) e v2 (oauth2)
- recursos principais: raw, items, tickets, users, documents, search, massive actions
- cliente v2 orientado a OpenAPI (`v2.call(operation_id, ...)`)
- ferramentas AI para tickets/users/entities
- observabilidade basica com correlation id e sanitizacao de headers
- testes iniciais com MockTransport
