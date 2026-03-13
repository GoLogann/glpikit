# Quickstart GraphQL

```python
from glpikit import GLPI

glpi = GLPI(base_url="https://glpi.example.com", mode="v1", auth={"user_token": "..."})

data = glpi.graphql.query("query { Ticket { id name } }")
print(data)
```

## Introspecao

```python
schema = glpi.graphql.schema()
print(schema.data.keys())
```

## Builder

```python
query = glpi.graphql.builder("Ticket").field("id").field("name").build()
print(glpi.graphql.query(query))
```
