from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLFloat
)

CpuTimesType = GraphQLObjectType(
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
        'guestNice': GraphQLField(GraphQLNonNull(GraphQLFloat)),
    }
)
