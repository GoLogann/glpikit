# Integration tests

These tests target a live GLPI instance and are skipped by default.

## Run with env vars

```bash
export GLPI_INTEGRATION_BASE_URL="https://your-glpi"
export GLPI_INTEGRATION_USER_TOKEN="..."
export GLPI_INTEGRATION_APP_TOKEN="..."
python -m pytest -q tests/integration
```

## Run Docker matrix helper

```bash
./scripts/run_integration_matrix.sh
```
