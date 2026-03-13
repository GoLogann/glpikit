# Roadmap 2 semanas (status atualizado em 13/03/2026)

Este documento consolida o plano de duas semanas com status real de execucao.

## Objetivo original

Fechar robustez de producao para GLPI com foco em:

- cobertura v2 orientada a OpenAPI
- confiabilidade (testes em GLPI real)
- compatibilidade plugin-aware
- operacao segura e observavel

## Status por frente

### 1) Cobertura v2 orientada a OpenAPI

Status: **concluido (MVP3.1)**

- `v2.call(operation_id, ...)` com mapeamento de path/query/header/cookie/body
- coercao de tipos baseada em schema OpenAPI
- parsing tipado de resposta com `v2.call_typed(...)`
- `v2.generated.<operationId>(...)` e `v2.adapter("Itemtype")` (best-effort)
- modelos de request/response gerados em runtime por operacao

Arquivos principais:

- `src/glpikit/v2/resources.py`
- `src/glpikit/v2/openapi.py`
- `src/glpikit/v2/typed.py`
- `src/glpikit/v2/generated/runtime.py`

Testes relacionados:

- `tests/test_v2_contract.py`
- `tests/test_v2_generated_and_adapters.py`
- `tests/test_policy_oauth_and_v2_typed.py`

### 2) Search metadata cache + bulk ergonomics

Status: **concluido (MVP3.1)**

- cache TTL para `list_search_options`
- resolucao de campos por nome/uid na DSL de busca
- iteradores (`iter_all`, `iter_search`, `aiter_search`)
- bulk operations com chunking, retry parcial e relatorio consolidado

Arquivos principais:

- `src/glpikit/resources/items.py`
- `src/glpikit/resources/search.py`
- `src/glpikit/utils/cache.py`
- `src/glpikit/utils/bulk.py`

Testes relacionados:

- `tests/test_items_advanced.py`
- `tests/test_async_client.py`

### 3) Integracao com GLPI real e CI

Status: **parcial (MVP3.2)**

Ja entregue:

- scaffold Docker (`docker/compose.glpi.yml`)
- testes de integracao smoke (`tests/integration/test_live_glpi.py`)
- workflow CI com job de integracao opcional (`.github/workflows/ci.yml`)
- helper de matriz (`scripts/run_integration_matrix.sh`)

Pendente para fechar 100%:

- matriz forte por versao GLPI/plugin com seed de dados
- cenarios de escrita end-to-end automatizados de forma deterministica
- isolamento de fixtures por entidade/perfil para evitar efeitos colaterais

### 4) Plugin-aware capabilities + safety

Status: **concluido (MVP3.2)**

- `capabilities()` com descoberta de plugins e itemtypes conhecidos
- `supports_graphql()`, `supports_v2()`, `supports_itemtype(...)`
- policy engine para operacoes destrutivas (`dry_run`, confirmacao)
- fallback automatico de auth/mode em `mode="auto"` (v1 <-> v2)

Arquivos principais:

- `src/glpikit/client.py`
- `src/glpikit/async_client.py`
- `src/glpikit/utils/capability.py`
- `src/glpikit/ai/policy.py`

Testes relacionados:

- `tests/test_sync_client.py`
- `tests/test_async_client.py`
- `tests/test_mvp_completion.py`
- `tests/test_policy_oauth_and_v2_typed.py`

### 5) Observabilidade + release readiness

Status: **quase concluido (MVP3.3)**

Ja entregue:

- hooks estruturados de observabilidade
- correlation id + redaction de headers sensiveis
- coletor de metricas por status/metodo/endpoint + latencia
- hooks opcionais para OpenTelemetry
- documentacao de uso atualizada

Pendente para fechar 100%:

- publicacao oficial no PyPI
- checklist final de release (tag semver, notas finais, automacao de publish)

## Backlog imediato (restante para 100%)

1. Integracao real forte em matriz GLPI/plugin com seed de dados e escrita automatizada.
2. Pipeline de release/publicacao (PyPI) totalmente operacional.

## Definicao de pronto (global)

- `python -m ruff check .` e `python -m pytest -q` verdes
- exemplos de docs executam sem ajuste manual
- mudancas de API publica com notas de migracao
- testes de integracao reais reproduziveis em ambiente limpo
