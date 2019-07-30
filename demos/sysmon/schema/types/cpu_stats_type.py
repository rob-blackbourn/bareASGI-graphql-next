from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull
)

from .long_type import GraphQLLong

CpuStatsType = GraphQLObjectType(
    name='CpuStats',
    fields=lambda: {
        'ctxSwitches': GraphQLField(GraphQLNonNull(GraphQLLong)),
        'interrupts': GraphQLField(GraphQLNonNull(GraphQLLong)),
        'softInterrupts': GraphQLField(GraphQLNonNull(GraphQLLong)),
        'syscalls': GraphQLField(GraphQLNonNull(GraphQLLong))
    }
)
