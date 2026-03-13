# Integration testing (GLPI real)

## Docker local

```bash
docker compose -f docker/compose.glpi.yml up -d
```

## Variaveis de ambiente

- `GLPI_INTEGRATION_BASE_URL`
- auth v1: `GLPI_INTEGRATION_USER_TOKEN`, `GLPI_INTEGRATION_APP_TOKEN`
- auth v2: `GLPI_INTEGRATION_CLIENT_ID`, `GLPI_INTEGRATION_CLIENT_SECRET`, `GLPI_INTEGRATION_USERNAME`, `GLPI_INTEGRATION_PASSWORD`

## Executar

```bash
python -m pytest -q tests/integration
```

Os testes fazem smoke de leitura para validar conectividade e capacidades.
