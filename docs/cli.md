# CLI

A CLI `glpikit` usa `GLPI.from_env()`.

## Variaveis basicas

- `GLPI_BASE_URL`
- `GLPI_MODE` (`v1`, `v2`, `auto`)
- credenciais (`GLPI_USER_TOKEN`/`GLPI_APP_TOKEN` ou `GLPI_CLIENT_ID` etc)

## Comandos

```bash
glpikit capabilities
glpikit tickets-get 123
glpikit search Ticket "email" --limit 5
glpikit v2-call getTicket --param id=123
glpikit documents-upload ./manual.pdf --name "Manual"
glpikit documents-download 55 --to ./downloads/manual.pdf
```
