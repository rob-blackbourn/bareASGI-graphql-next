# type: ignore
# pylint: disable=no-self-argument

import asyncio
from datetime import datetime
from graphene import ObjectType, String, Schema, Field

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
