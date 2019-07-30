from graphql import GraphQLObjectType

from .system_queries import LatestQuery

RootQueryType = GraphQLObjectType(
    name='Queries',
    fields=lambda: {
        'latest': LatestQuery,
    }
)
