"""
System queries
"""

from graphql import GraphQLField

from ..types.system_type import SystemType
from ...resolvers.query_resolver import get_latest

# pylint: disable=invalid-name
LatestQuery = GraphQLField(
    SystemType,
    description="Get the latest data",
    resolve=get_latest
)
