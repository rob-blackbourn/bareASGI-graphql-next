"""
GraphQL controller
"""

import logging

from typing import Optional

from graphql import GraphQLSchema
from bareasgi import Application
from baretypes import (
    Scope,
    Info,
    HttpMiddlewareCallback
)

from .controller import GraphQLController

logger = logging.getLogger(__name__)


def add_graphql_next(
        app: Application,
        schema: GraphQLSchema,
        path_prefix: str = '',
        rest_middleware: Optional[HttpMiddlewareCallback] = None,
        view_middleware: Optional[HttpMiddlewareCallback] = None,
        graphql_middleware=None,
        ping_interval: float = 10
) -> None:
    """Add graphql support to an bareASGI application.

    :param app: The bareASGI application.
    :param schema: The GraphQL schema to use.
    :param path_prefix: An optional path prefix from which to provide endpoints.
    :param rest_middleware: Middleware for the rest end points.
    :param view_middleware: Middleware from the GraphiQL end point.
    :param graphql_middleware: Middleware for graphql-core-next.
    :param subscription_expiry: The time to wait before abandoning an unused subscription.
    :return: Returns the constructed controller.
    """

    # pylint: disable=unused-argument
    async def start_graphql(scope: Scope, info: Info, request) -> None:
        """Start the GraphQL controller"""

        logger.debug('Starting the GraphQL controller')

        controller = GraphQLController(
            schema,
            path_prefix,
            graphql_middleware,
            ping_interval
        )
        controller.add_routes(app, path_prefix, rest_middleware, view_middleware)
        info['graphql_controller'] = controller

    # pylint: disable=unused-argument
    async def stop_graphql(scope: Scope, info: Info, request) -> None:
        """Stop the GraphQL controller"""

        logger.debug('Stopping the GraphQL controller')

        graphql_controller: GraphQLController = info['graphql_controller']
        await graphql_controller.shutdown()

    app.startup_handlers.append(start_graphql)
    app.shutdown_handlers.append(stop_graphql)
