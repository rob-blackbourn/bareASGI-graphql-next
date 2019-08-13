"""
GraphQL schema
"""

from graphql import (
    GraphQLSchema,
)

from .queries import RootQueryType
# from .mutations import RootMutationType
from .subscriptions import RootSubscriptionType

# pylint: disable=invalid-name
schema = GraphQLSchema(
    query=RootQueryType,
    # mutation=RootMutationType,
    subscription=RootSubscriptionType
)
