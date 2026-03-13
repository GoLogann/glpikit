# Integration tests

These tests target a live GLPI instance and are skipped by default.

## Run with env vars

```bash
export GLPI_INTEGRATION_BASE_URL="https://your-glpi"
export GLPI_INTEGRATION_USER_TOKEN="..."
export GLPI_INTEGRATION_APP_TOKEN="..."
export GLPI_INTEGRATION_CLIENT_ID="..."
export GLPI_INTEGRATION_CLIENT_SECRET="..."
# optional for password grant:
export GLPI_INTEGRATION_USERNAME="..."
export GLPI_INTEGRATION_PASSWORD="..."
python -m pytest -q tests/integration
```

`GLPI_INTEGRATION_BASE_URL` must be the instance base URL, without `/apirest.php`.

## Run Docker matrix helper

```bash
./scripts/run_integration_matrix.sh
```
