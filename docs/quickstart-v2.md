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

# camada generated: operationId como metodo
print(glpi.v2.generated.getTicket(id=10))

# adapter por itemtype (best-effort por naming da spec)
tickets = glpi.v2.adapter("Ticket")
print(tickets.list())
```

## Descoberta da spec

- `glpi.v2.load_openapi()`
- `glpi.v2.operations()`
- `glpi.v2.generated.operations()`
