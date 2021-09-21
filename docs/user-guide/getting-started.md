# Getting Started

A utility function `add_graphql_next` is provided.

```python
from bareasgi import Application
from bareasgi_graphql_next import add_graphql_next
from star_wars.star_wars_schema import star_wars_schema

import uvicorn

app = Application()
add_graphql_next(app, star_wars_schema)

uvicorn.run(app, port=9009)
```

For graphene the utility function `add_graphene` is provided.

```python
import asyncio
from datetime import datetime

from bareasgi import Application
from bareasgi_graphql_next.graphene import add_graphene
from graphene import ObjectType, String, Schema, Field
import uvicorn

# All schema require a query.
class Query(ObjectType):
    hello = String()

    def resolve_hello(root, info):
        return 'Hello, world!'

class Subscription(ObjectType):
    time = Field(String)

    async def subscribe_time(root, info):
        while True:
            yield { 'time': datetime.now().isoformat()}
            await asyncio.sleep(1)

SCHEMA = Schema(query=Query, subscription=Subscription)

app = Application()
add_graphene(app, SCHEMA)

uvicorn.run(app, port=9009)
```