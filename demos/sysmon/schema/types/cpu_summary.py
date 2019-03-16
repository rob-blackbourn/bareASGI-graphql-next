from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLFloat
)

from .cpu_stats import CpuStats
from .cpu_times import CpuTimes

CpuSummary = GraphQLObjectType(
    name='CpuSummary',
    fields=lambda: {
        'percent': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'stats': GraphQLField(GraphQLNonNull(CpuStats)),
        'times': GraphQLField(GraphQLNonNull(CpuTimes))
    }
)
