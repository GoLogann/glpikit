# Troubleshooting auth

## V1

- erro `AuthenticationError`: confira `user_token` ou `username/password`
- erro de permissao: confira perfil/entidade no GLPI
- se houver expiracao frequente, valide timeout de sessao no servidor

## V2

- confira `client_id`/`client_secret`
- valide grant suportado no seu ambiente
- para refresh, garanta `refresh_token` valido no construtor

## Diagnostico rapido

- `glpi.capabilities()`
- `glpi.v2.load_openapi()` (modo v2)
