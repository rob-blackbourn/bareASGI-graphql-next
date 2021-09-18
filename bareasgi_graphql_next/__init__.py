"""bareASGI-graphql-next"""

import logging

from .graphql.controller import GraphQLController
from .graphql.helpers import add_graphql_next

__all__ = [
    'GraphQLController',
    'add_graphql_next'
]

logging.getLogger("bareasgi_graphql_next").addHandler(logging.NullHandler())
