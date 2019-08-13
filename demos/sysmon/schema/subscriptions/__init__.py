"""
GraphQL Subscriptions
"""

import graphql

from .system_subscriptions import SystemSubscription

# pylint: disable=invalid-name
RootSubscriptionType = graphql.GraphQLObjectType(
    "Subscriptions",
    {
        "system": SystemSubscription
    }
)

__all__ = ['RootSubscriptionType']
