from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLString,
)

from .cpu_type import CpuType

SystemType = GraphQLObjectType(
    name='System',
    fields=lambda: {
        'timestamp': GraphQLField(GraphQLNonNull(GraphQLString)),
        'cpu': GraphQLField(GraphQLNonNull(CpuType)),
    }
)
