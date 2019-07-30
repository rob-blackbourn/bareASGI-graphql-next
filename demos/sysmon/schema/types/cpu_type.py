from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLFloat,
    GraphQLInt,
    GraphQLList
)

from .cpu_stats_type import CpuStatsType
from .core_type import CoreType

CpuType = GraphQLObjectType(
    name='Cpu',
    fields=lambda: {
        'count': GraphQLField(GraphQLNonNull(GraphQLInt)),
        'percent': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'cores': GraphQLField(GraphQLList(GraphQLNonNull(CoreType))),
        'stats': GraphQLField(GraphQLNonNull(CpuStatsType)),
    }
)
