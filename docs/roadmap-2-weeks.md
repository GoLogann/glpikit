# Roadmap 2 semanas (MVP3.1 -> MVP3.3)

Periodo sugerido: 16 a 27 de marco de 2026.

## Objetivo

Fechar robustez de producao para GLPI com foco em:

- cobertura v2 orientada a OpenAPI
- confiabilidade (testes em GLPI real)
- compatibilidade plugin-aware
- operacao segura e observavel

## Sprint breakdown

### Semana 1 (16-20/03/2026): base tecnica e cobertura v2

#### PR 1 - OpenAPI coverage v2 (MVP3.1)

Escopo:

- fortalecer `v2.call(operation_id, ...)` para todos verbos e parametros
- mapear path/query/body com validacao minima
- adicionar utilitario para listar operacoes faltantes por `operationId`
- criar smoke tests para chamadas de operacao com spec mock

Arquivos principais:

- `src/glpikit/v2/resources.py`
- `src/glpikit/v2/openapi.py`
- `tests/test_v2_openapi_operations.py` (novo)

Criterio de aceite:

- `v2.operations()` lista operacoes reais da spec
- `v2.call(...)` executa GET/POST/PUT/PATCH/DELETE com parametros corretos
- cobertura de testes para fluxo de erro e sucesso

#### PR 2 - Search metadata cache + bulk ergonomics (MVP3.1)

Escopo:

- cache TTL para `list_search_options`
- API de busca com resolucao de campo por nome/uid
- utilitarios de lote: chunk processing e resumo de resultados

Arquivos principais:

- `src/glpikit/resources/search.py`
- `src/glpikit/resources/items.py`
- `src/glpikit/utils/` (cache e bulk helpers)
- `tests/test_search_cache.py` (novo)

Criterio de aceite:

- repeticao de chamadas de search options reduz requests redundantes
- campos podem ser passados por nome amigavel quando metadata estiver no cache
- resultados de lote retornam resumo consistente de sucesso/falha

### Semana 2 (23-27/03/2026): producao, compatibilidade e release prep

#### PR 3 - Integration tests com GLPI em Docker (MVP3.2)

Escopo:

- stack Docker para GLPI + DB em ambiente de teste
- testes de integracao para auth v1, auth v2, tickets, search, documents
- profile de CI para rodar suite de integracao opcionalmente

Arquivos principais:

- `docker/` (novo)
- `tests/integration/` (novo)
- `.github/workflows/ci.yml` ou equivalente (novo/ajuste)

Criterio de aceite:

- suite de integracao sobe ambiente do zero
- casos criticos passam em GLPI real
- fluxo local documentado em README/docs

#### PR 4 - Plugin-aware capabilities e safety policies (MVP3.2)

Escopo:

- capabilities com descoberta real de recursos disponiveis
- melhoria de `supports_itemtype` com fallback inteligente
- policies de seguranca para operacoes destrutivas (`dry_run`, confirmacao)

Arquivos principais:

- `src/glpikit/client.py`
- `src/glpikit/async_client.py`
- `src/glpikit/utils/capability.py`
- `src/glpikit/ai/safe.py`
- `tests/test_capabilities_plugins.py` (novo)

Criterio de aceite:

- `capabilities()` reflete a instancia real do GLPI
- plugin itemtype tem comportamento previsivel
- operacoes destrutivas podem ser bloqueadas por policy

#### PR 5 - Observabilidade + release readiness (MVP3.3)

Escopo:

- logging estruturado padrao de SDK
- OpenTelemetry hooks opcionais
- documentacao final de uso (sync/async, auth, plugin, troubleshooting)
- checklist de release (semver, changelog, empacotamento)

Arquivos principais:

- `src/glpikit/transport/hooks.py`
- `docs/*.md`
- `CHANGELOG.md`
- `pyproject.toml`

Criterio de aceite:

- tracing pode ser habilitado sem quebrar API publica
- docs cobrem quickstart + troubleshooting + operacao avancada
- pacote pronto para tag/release

## Backlog imediato (pos 2 semanas)

- OAuth2 authorization code + PKCE helper
- CLI oficial (`glpikit ...`)
- adaptadores nativos para LangChain/LangGraph/MCP
- contract tests contra multiplas versoes de GLPI

## Definicao de pronto (global)

- `ruff` e `pytest` verdes
- exemplos de docs executam sem ajuste manual
- mudancas de API publica com notas de migracao
- PRs pequenos e revisaveis (evitar mega-PR)
