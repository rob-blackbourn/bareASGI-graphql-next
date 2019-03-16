from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLList
)

from .long import GraphQLLong
from .cpu_summary import CpuSummary

CpuSammryList = GraphQLObjectType(
    name='CpuSummaryList',
    fields=lambda: {
        'count': GraphQLField(GraphQLNonNull(GraphQLLong)),
        'cpu': GraphQLField(GraphQLNonNull(GraphQLList(GraphQLNonNull(CpuSummary))))
    }
)
