"""
System subscriptions
"""

from graphql import GraphQLField
from ..types import SystemType
from ...resolvers.subscription_resolver import subscribe_to_systems, resolve_subscriptions

# pylint: disable=invalid-name
SystemSubscription = GraphQLField(
    SystemType,
    description="Subscribe to changes to order sets on the EMS queue",
    subscribe=subscribe_to_systems,
    resolve=resolve_subscriptions,
)
