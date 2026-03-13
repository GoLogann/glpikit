# glpikit

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.1.0-informational)](pyproject.toml)
![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)

Python SDK para GLPI com suporte unificado a REST API v1 (session token), REST API v2 (OAuth2) e GraphQL read-only.

## Table of Contents

- [About](#about)
- [Development](#development)
- [Installation](#installation)
- [Usage](#usage)
- [CLI](#cli)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contact](#contact)
- [Contributors](#contributors)
- [Credits](#credits)
- [Contributing](#contributing)

## About

`glpikit` (GLPI + kit) foi desenhado como um SDK Python idiomatico para automacao de service desk, backend integrations e agentes de IA.

A biblioteca expõe uma API publica unica e esconde a complexidade de autenticacao e superfícies de API do GLPI:

- engine v1 (session-based)
- engine v2 (OAuth2/OpenAPI)
- camada GraphQL read-only
- cliente sync (`GLPI`) e async (`AsyncGLPI`)

## Development

`glpikit` esta em desenvolvimento ativo.

Principais direcoes atuais:

- cobertura ampla da API v1/v2 com interfaces Pythonicas
- recursos de dominio (tickets, users, documents, entities etc.)
- robustez operacional (retry, policy engine, observability)
- ergonomia para agentes (AI tools, schemas, integrations MCP/LangChain/LangGraph)

Stack principal:

- `httpx` para transporte HTTP sync/async
- `pydantic` para modelos e validacao tipada

## Installation

No momento, a forma recomendada e instalar via source:

```bash
pip install -e .[dev]
```

Requer Python 3.10+.

## Usage

Importante: use `base_url` da instancia sem sufixo `/apirest.php`.

### REST v1 (App-Token + User-Token)

```python
from glpikit import GLPI

glpi = GLPI(
    base_url="https://glpi.example.com",
    mode="v1",
    auth={
        "app_token": "...",
        "user_token": "...",
    },
)

ticket = glpi.tickets.create(
    title="Falha no e-mail",
    description="Usuario sem acesso ao webmail",
    entities_id=70,
    requesttypes_id=7,
    itilcategories_id=19,
    urgency=3,
    impact=3,
    priority=3,
)

print(ticket.id)
glpi.close()
```

### REST v2 (OpenAPI operation_id)

```python
from glpikit import GLPI

glpi = GLPI(
    base_url="https://glpi.example.com",
    mode="v2",
    auth={
        "client_id": "...",
        "client_secret": "...",
        "username": "...",
        "password": "...",
    },
)

ops = glpi.v2.operations()
ticket = glpi.v2.call("getTicket", id=123)
print(len(ops), ticket)
glpi.close()
```

### Async

```python
from glpikit import AsyncGLPI

async def main():
    async with AsyncGLPI(
        base_url="https://glpi.example.com",
        mode="v1",
        auth={"app_token": "...", "user_token": "..."},
    ) as glpi:
        ticket = await glpi.tickets.get(123)
        print(ticket.id)
```

## CLI

Comandos principais:

```bash
glpikit capabilities
glpikit tickets-get 123
glpikit search Ticket "email" --limit 5
glpikit v2-operations
glpikit v2-call getTicket --param id=123
glpikit documents-upload ./manual.pdf --name "Manual"
glpikit documents-download 55 --to ./downloads/manual.pdf
```

## Testing

### Unit tests

```bash
python -m ruff check .
python -m pytest -q
```

### Integration tests (GLPI real)

Variaveis esperadas:

- `GLPI_INTEGRATION_BASE_URL`
- `GLPI_INTEGRATION_USER_TOKEN`
- `GLPI_INTEGRATION_APP_TOKEN`
- opcional v2: `GLPI_INTEGRATION_CLIENT_ID`, `GLPI_INTEGRATION_CLIENT_SECRET`, `GLPI_INTEGRATION_USERNAME`, `GLPI_INTEGRATION_PASSWORD`

Observacao: `GLPI_INTEGRATION_BASE_URL` deve ser a URL base da instancia, sem `/apirest.php`.

Execucao:

```bash
python -m pytest -q tests/integration
```

Helper de matriz Docker:

```bash
./scripts/run_integration_matrix.sh
```

## Documentation

- [Quickstart v1](docs/quickstart-v1.md)
- [Quickstart v2](docs/quickstart-v2.md)
- [Quickstart GraphQL](docs/quickstart-graphql.md)
- [Async usage](docs/async-usage.md)
- [Agents/LLM integration](docs/agents-llm-integration.md)
- [CLI](docs/cli.md)
- [OAuth2 PKCE](docs/oauth2-pkce.md)
- [Integration testing](docs/integration-testing.md)
- [Contract tests](docs/contract-tests.md)
- [Troubleshooting auth](docs/troubleshooting-auth.md)
- [Migration guide](docs/migration-guide.md)

## Contact

- Abra uma issue para bugs e propostas de melhoria.
- Para discussoes tecnicas maiores, use pull request com design notes curtas.

## Contributors

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/GoLogann"><img src="https://github.com/GoLogann.png?size=100" width="100px;" alt=""/><br /><sub><b>GoLogann</b></sub></a><br /><a href="https://github.com/GoLogann" title="Code">💻</a> <a href="https://github.com/GoLogann" title="Documentation">📖</a></td>
  </tr>
</table>
<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome.

## Credits

Criador e idealizador do projeto:

- [Logan Cardoso (GoLogann)](https://github.com/GoLogann)
- [LinkedIn](https://www.linkedin.com/in/logan-cardoso/)

## Contributing

Contribuicoes sao bem-vindas.

Fluxo recomendado:

1. Abra uma issue curta com contexto.
2. Faça fork/branch com escopo pequeno.
3. Rode `ruff check .` e `pytest -q`.
4. Abra PR com descricao objetiva das mudancas.
