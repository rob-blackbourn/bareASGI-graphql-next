from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLFloat
)

from .long import GraphQLLong

CpuTimes = GraphQLObjectType(
    name='CpuTimes',
    fields=lambda: {
        'user': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'nice': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'system': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'idle': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'iowait': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'irq': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'softirq': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'steal': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'guest': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'guest_nice': GraphQLField(GraphQLNonNull(GraphQLFloat)),
    }
)
