from typing import Any
from graphql.type import GraphQLScalarType
from graphql.error import INVALID
from graphql.pyutils import is_integer
from graphql.language.ast import IntValueNode

MAX_LONG = 2 ** 53 - 1
MIN_LONG = -(2 ** 53)

def is_valid_long(value: int):
    return MIN_LONG <= value <= MAX_LONG

def serialize_long(value: Any) -> int:
    if isinstance(value, bool):
        return 1 if value else 0

    try:
        if isinstance(value, int):
            num = value
        elif isinstance(value, float):
            num = int(value)
            if num != value:
                raise ValueError()
        elif not value and isinstance(value, str):
            value = ''
            raise ValueError()
        else:
            num = int(value)
            float_value = float(value)
            if num != float_value:
                raise ValueError()
    except (OverflowError, ValueError, TypeError):
        raise TypeError(f'Long cannot represent non-integer value: {value:!r}')

    if not is_valid_long(num):
        raise TypeError(f'Long cannot represent non 53-bit signed integer value: {value:!r}')

    return num

def coerce_long(value: Any) -> int:
    if not is_integer(value):
        raise TypeError(f'Long cannot represent non-integer value: {value:!r}')
    if not is_valid_long(value):
        raise TypeError(f'Long cannot represent non 53-bit signed integer value: {value: !r}')
    return int(value)

def parse_long_literal(ast, _variables=None):
    if isinstance(ast, IntValueNode):
        num = int(ast.value)
        if is_valid_long(num):
            return num
    return INVALID

GraphQLLong = GraphQLScalarType(
    name='Long',
    description="The 'Long' scalar type represents"
                " non-fractional signed whole numeric values."
                " Int can represent values between -(2^53) and 2^53 - 1.",
    serialize=serialize_long,
    parse_value=coerce_long,
    parse_literal=parse_long_literal
)