# Quickstart v1

```python
from glpikit import GLPI

glpi = GLPI(
    base_url="https://glpi.example.com",
    mode="v1",
    auth={"app_token": "...", "user_token": "..."},
)

ticket = glpi.tickets.create(
    title="Falha no e-mail",
    description="Usuario sem acesso",
    urgency=3,
)
print(ticket.id)
```

## Operacoes uteis

- `glpi.items.get("Ticket", 123)`
- `glpi.items.list_search_options("Ticket")`
- `glpi.search("Ticket").where("name", "contains", "mail").limit(10).run()`
