# Async usage

```python
from glpikit import AsyncGLPI

async def main():
    async with AsyncGLPI(
        base_url="https://glpi.example.com",
        mode="v2",
        auth={"client_id": "...", "client_secret": "...", "username": "...", "password": "..."},
    ) as glpi:
        ticket = await glpi.tickets.get(123)
        print(ticket)
```

## Recursos async

- `await glpi.tickets.create(...)`
- `await glpi.documents.upload(...)`
- `await glpi.v2.call(...)`
- `await glpi.capabilities_async()`
