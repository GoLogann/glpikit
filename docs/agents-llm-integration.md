# Agents and LLM integration

## Tooling pronta

```python
from glpikit import GLPI
from glpikit.ai import (
    create_ticket_tool,
    search_ticket_tool,
    get_ticket_tool,
    update_ticket_tool,
    add_followup_tool,
    search_user_tool,
    get_entity_tool,
)

glpi = GLPI.from_env()

tools = {
    "create_ticket": create_ticket_tool(glpi),
    "search_ticket": search_ticket_tool(glpi),
    "get_ticket": get_ticket_tool(glpi),
    "update_ticket": update_ticket_tool(glpi),
    "add_followup": add_followup_tool(glpi),
    "search_user": search_user_tool(glpi),
    "get_entity": get_entity_tool(glpi),
}
```

## Seguranca

- use `whitelist_payload` para limitar campos aceitos
- use `diff_payload` para explicar mudancas ao usuario
- exija confirmacao para acoes destrutivas com `require_confirmation`
