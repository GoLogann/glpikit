# OAuth2 Authorization Code + PKCE

## Gerar verifier/challenge

```python
from glpikit import GLPI

verifier, challenge = GLPI.oauth_pkce_pair()
```

## Montar URL de autorizacao

```python
url = GLPI.oauth_authorization_url(
    authorize_url="https://auth.example/authorize",
    client_id="client-id",
    redirect_uri="https://app.example/callback",
    scope="openid profile",
    state="nonce-123",
    code_challenge=challenge,
)
```

## Trocar code por token

Passe no construtor:

- `authorization_code`
- `redirect_uri`
- `code_verifier`
