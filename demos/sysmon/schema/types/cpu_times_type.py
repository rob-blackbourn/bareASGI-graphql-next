"""
CPU Times type
"""

from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLFloat
)

# pylint: disable=invalid-name
CpuTimesType = GraphQLObjectType(
    name='CpuTimes',
    fields=lambda: {
        'user': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'nice': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'system': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'idle': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'iowait': GraphQLField(GraphQLFloat),
        'irq': GraphQLField(GraphQLFloat),
        'softirq': GraphQLField(GraphQLFloat),
        'steal': GraphQLField(GraphQLFloat),
        'guest': GraphQLField(GraphQLFloat),
        'guestNice': GraphQLField(GraphQLFloat),
    }
)
