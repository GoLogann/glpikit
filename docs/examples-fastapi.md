# FastAPI example

```python
from fastapi import FastAPI
from glpikit import GLPI

app = FastAPI()
glpi = GLPI.from_env()

@app.get('/tickets/{ticket_id}')
def get_ticket(ticket_id: int):
    ticket = glpi.tickets.get(ticket_id)
    return ticket.model_dump(exclude_none=True)
```

## Produção

- habilite `enable_observability=True`
- defina timeout/retry adequados por operacao
- logue exceptions `GLPIError` com `to_prompt_context()`
