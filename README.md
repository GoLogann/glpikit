# glpikit

SDK Python para GLPI com suporte unificado a API v1 (session token), API v2 (OAuth2) e GraphQL read-only.

## Status

Projeto em construção com base pronta para os 3 MVPs:

- cliente `GLPI` (sync) e `AsyncGLPI` (async)
- autenticação v1 (session) e v2 (OAuth2)
- recursos `raw`, `items`, `tickets`, `users`, `documents`, `search`, `massive_actions`
- recursos de domínio (entities, profiles, groups, computers, software etc.)
- GraphQL read-only com introspecao e builder
- `v2.call(operation_id, ...)` orientado a OpenAPI
- erros tipados
- ferramentas AI (`create/get/update/search ticket`, `add_followup`, `search_user`, `get_entity`)
- hooks de observabilidade (correlation id + sanitizacao de headers)
- suporte OAuth2 com Authorization Code + PKCE helpers
- CLI oficial (`glpikit`)
- iteradores de paginação, bulk operations e cache TTL de `searchOptions`

## Instalação (desenvolvimento)

```bash
pip install -e .[dev]
```

## Exemplo rápido

```python
from glpikit import GLPI

glpi = GLPI(
    base_url="https://glpi.example.com",
    auth={"app_token": "app", "user_token": "user"},
    mode="v1",
)

ticket = glpi.tickets.create(
    title="Falha no e-mail",
    description="Usuário sem acesso",
    urgency=3,
)
print(ticket.id)
```

## CLI

```bash
glpikit capabilities
glpikit tickets-get 123
glpikit search Ticket \"email\" --limit 5
glpikit v2-call getTicket --param id=123
```

## Integração real (Docker)

Arquivo base: `docker/compose.glpi.yml`.

Testes de integração (quando variáveis `GLPI_INTEGRATION_*` estiverem configuradas):

```bash
python -m pytest -q tests/integration
```

## Documentacao

- [Quickstart v1](docs/quickstart-v1.md)
- [Quickstart v2](docs/quickstart-v2.md)
- [Quickstart GraphQL](docs/quickstart-graphql.md)
- [Async usage](docs/async-usage.md)
- [Agents/LLM integration](docs/agents-llm-integration.md)
- [Troubleshooting auth](docs/troubleshooting-auth.md)
- [Migration guide](docs/migration-guide.md)
- [Roadmap 2 semanas](docs/roadmap-2-weeks.md)
- [CLI](docs/cli.md)
- [OAuth2 PKCE](docs/oauth2-pkce.md)
- [Integration testing](docs/integration-testing.md)
- [Contract tests](docs/contract-tests.md)
