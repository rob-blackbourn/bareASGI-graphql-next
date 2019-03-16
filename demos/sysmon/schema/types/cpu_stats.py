from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull
)

from .long import GraphQLLong

CpuStats = GraphQLObjectType(
    name='CpuStats',
    fields=lambda: {
        'ctx_switches': GraphQLField(GraphQLNonNull(GraphQLLong)),
        'interrupts': GraphQLField(GraphQLNonNull(GraphQLLong)),
        'soft_interrupts': GraphQLField(GraphQLNonNull(GraphQLLong)),
        'syscalls': GraphQLField(GraphQLNonNull(GraphQLLong))
    }
)
