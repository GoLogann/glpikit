# Contract tests (OpenAPI-driven)

The project includes spec-driven contract tests for v2 in `tests/test_v2_contract.py`.

## What it validates

- operation indexing from OpenAPI
- minimum argument generation per operation
- execution of every operation id in a fixture spec via `v2.call(...)`
- typed parsing with `v2.call_typed(...)` for composed schemas (`allOf`, `oneOf`)

## Run

```bash
python -m pytest -q tests/test_v2_contract.py
```
