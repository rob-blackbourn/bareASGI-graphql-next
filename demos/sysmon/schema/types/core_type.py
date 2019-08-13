"""
Core type
"""

from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLFloat,
)

from .cpu_times_type import CpuTimesType

# pylint: disable=invalid-name
CoreType = GraphQLObjectType(
    name='Core',
    fields=lambda: {
        'percent': GraphQLField(GraphQLNonNull(GraphQLFloat)),
        'times': GraphQLField(GraphQLNonNull(CpuTimesType)),
    }
)
