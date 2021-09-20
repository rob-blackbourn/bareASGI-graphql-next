"""
System type
"""

from graphql import (
    GraphQLObjectType,
    GraphQLField,
    GraphQLNonNull,
    GraphQLString,
)

from .cpu_type import CpuType

# pylint: disable=invalid-name
SystemType = GraphQLObjectType(
    name='System',
    fields=lambda: {
        'timestamp': GraphQLField(GraphQLNonNull(GraphQLString)),
        'cpu': GraphQLField(GraphQLNonNull(CpuType)),
    }
)

"""
{
    'timestamp': datetime.datetime(2021, 9, 19, 10, 15, 24, 603890),
    'cpu': {
        'count': 4,
        'percent': 57.6,
        'cores': [
            {
                'percent': 81.4,
                'times': {
                    'user': 28407.18,
                    'nice': 0.0,
                    'system': 12325.14,
                    'idle': 83567.37
                }
            },
            {
                'percent': 33.7,
                'times': {
                    'user': 8680.27,
                    'nice': 0.0,
                    'system': 3561.52,
                    'idle': 112043.48
                }
            },
            {
                'percent': 85.0,
                'times': {
                    'user': 28394.75,
                    'nice': 0.0,
                    'system': 9387.28,
                    'idle': 86503.27
                }
            },
            {
                'percent': 30.0,
                'times': {
                    'user': 8061.73,
                    'nice': 0.0,
                    'system': 3244.96,
                    'idle': 112978.54
                }
            }
        ],
        'stats': {
            'ctxSwitches': 32337,
            'interrupts': 379352,
            'softInterrupts': 399721283,
            'syscalls': 526632
        }
    }
}
"""
