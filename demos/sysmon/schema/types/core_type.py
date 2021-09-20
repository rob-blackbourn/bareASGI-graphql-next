"""
Core type
"""

from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLFloat,
    GraphQLInt
)

from .cpu_times_type import CpuTimesType

# pylint: disable=invalid-name
CoreType = GraphQLObjectType(
    name='Core',
    fields=lambda: {
        'core': GraphQLField(GraphQLNonNull(GraphQLInt)),
        'percent': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'times': GraphQLField(GraphQLNonNull(CpuTimesType)),
    }
)
