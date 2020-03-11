"""
GraphQL controller
"""

import logging

from typing import Optional

from graphene import Schema
from bareasgi import Application
from baretypes import (
    Scope,
    Info,
    HttpMiddlewareCallback
)

from .controller import GrapheneController

logger = logging.getLogger(__name__)


def add_graphene(
        app: Application,
        schema: Schema,
        path_prefix: str = '',
        rest_middleware: Optional[HttpMiddlewareCallback] = None,
        view_middleware: Optional[HttpMiddlewareCallback] = None,
        graphql_middleware=None,
        ping_interval: float = 10
) -> None:
    """Add graphql support to an bareASGI application.
    
    Args:
        app (Application): The bareASGI application.
        schema (Schema): The Graphene schema to use.
        path_prefix (str, optional): An optional path prefix from which to
            provide endpoints. Defaults to ''.
        rest_middleware (Optional[HttpMiddlewareCallback], optional): Middleware
            for the rest end points. Defaults to None.
        view_middleware (Optional[HttpMiddlewareCallback], optional): Middleware
            for the GraphiQL end point. Defaults to None.
        graphql_middleware ([type], optional): Middleware for graphql-core-next.
            Defaults to None.
        ping_interval (float, optional): The time to wait before abandoning an unused subscription. Defaults to 10.
    """
    # pylint: disable=unused-argument
    async def start_graphql(scope: Scope, info: Info, request) -> None:
        """Start the GraphQL controller"""

        logger.debug('Starting the GraphQL controller')

        controller = GrapheneController(
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

        graphql_controller: GrapheneController = info['graphql_controller']
        await graphql_controller.shutdown()

    app.startup_handlers.append(start_graphql)
    app.shutdown_handlers.append(stop_graphql)
