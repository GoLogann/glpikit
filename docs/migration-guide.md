# Migration guide

## De scripts requests para glpikit

Antes:

```python
import requests
requests.get("https://.../apirest.php/Ticket/1", headers={...})
```

Depois:

```python
from glpikit import GLPI
glpi = GLPI(...)
ticket = glpi.tickets.get(1)
```

## Passos recomendados

1. mover auth para `GLPI(...)`
2. trocar chamadas HTTP por recursos (`tickets`, `users`, `documents`)
3. manter excecoes customizadas (`GLPIError` e subclasses)
4. usar `raw` apenas para casos de plugin/edge case
