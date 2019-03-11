import asyncio
from datetime import datetime
from graphql import (
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString
)


def resolve_time(root, info):
    print('Resolving time')
    return datetime.now().isoformat()


async def subscribe_time(root, info):
    print('Subscribing time')
    while True:
        yield {"time": datetime.now().isoformat()}
        print('Sleeping')
        await asyncio.sleep(1)
    print('Unsubscribing time')


schema = GraphQLSchema(
    query=GraphQLObjectType(
        "RootQueryType",
        {
            "time": GraphQLField(
                GraphQLNonNull(GraphQLString), resolve=resolve_time
            )
        },
    ),
    subscription=GraphQLObjectType(
        "RootSubscriptionType",
        {
            "time": GraphQLField(
                GraphQLNonNull(GraphQLString), subscribe=subscribe_time
            )
        },
    ),
)
