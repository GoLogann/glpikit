# Quickstart v2

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

# recurso direto
print(glpi.v2.get("Ticket", 10))

# chamada por operationId (OpenAPI)
print(glpi.v2.call("getTicket", id=10))
```

## Descoberta da spec

- `glpi.v2.load_openapi()`
- `glpi.v2.operations()`
