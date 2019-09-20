"""The schema for the time subscription"""

import asyncio
from datetime import datetime

from graphql import (
    GraphQLField,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString
)

def query_time(_root, _info):
    """Query time is an iso string"""
    print('Resolving time')
    return datetime.now().isoformat()


async def subscribe_time(_root, _info):
    """Start the time subscription"""
    print('Subscribing time')
    while True:
        yield {"time": datetime.now().isoformat()}
        print('Sleeping')
        await asyncio.sleep(1)
    print('Unsubscribing time')

# pylint: disable=invalid-name
schema = GraphQLSchema(
    query=GraphQLObjectType(
        "RootQueryType",
        {
            "time": GraphQLField(
                GraphQLNonNull(GraphQLString), resolve=query_time
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
