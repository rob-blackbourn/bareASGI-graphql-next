import graphql

from .system_subscriptions import SystemSubscription

RootSubscriptionType = graphql.GraphQLObjectType(
    "Subscriptions",
    {
        "system": SystemSubscription
    }
)

__all__ = ['RootSubscriptionType']
