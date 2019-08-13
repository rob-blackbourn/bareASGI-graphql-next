"""
GraphQL queries
"""

from graphql import GraphQLObjectType

from .system_queries import LatestQuery

# pylint: disable=invalid-name
RootQueryType = GraphQLObjectType(
    name='Queries',
    fields=lambda: {
        'latest': LatestQuery,
    }
)
