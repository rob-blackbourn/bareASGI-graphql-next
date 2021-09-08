"""
GraphQL controller
"""

import json
import logging
from typing import Any, Callable, Optional

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
        ping_interval: float = 10,
        loads: Callable[[str], Any] = json.loads,
        dumps: Callable[[Any], str] = json.dumps
) -> None:
    """Add graphql support to an bareASGI application.

    Args:
        app (Application): The bareASGI application.
        schema (GraphQLSchema): The GraphQL schema to use.
        path_prefix (str, optional): An optional path prefix from which to
            provide endpoints. Defaults to ''.
        rest_middleware (Optional[HttpMiddlewareCallback], optional): Middleware
            for the rest end points. Defaults to None.
        view_middleware (Optional[HttpMiddlewareCallback], optional): Middleware
            for the GraphiQL end point. Defaults to None.
        graphql_middleware ([type], optional): Middleware for graphql-core-next.
            Defaults to None.
        ping_interval (float, optional): The time to wait before abandoning an
            unused subscription. Defaults to 10.
        loads (Callable[[str], Any], optional): The function to convert a
            JSON string to an object. Defaults to json.loads.
        dumps (Callable[[Any], str], optional): The function to convert an
            object to a JSON string. Defaults to json.dumps.
    """
    # pylint: disable=unused-argument
    async def start_graphql(scope: Scope, info: Info, request) -> None:
        """Start the GraphQL controller"""

        logger.debug('Starting the GraphQL controller')

        controller = GraphQLController(
            schema,
            path_prefix,
            graphql_middleware,
            ping_interval,
            loads,
            dumps
        )
        controller.add_routes(
            app,
            path_prefix,
            rest_middleware, view_middleware
        )
        assert info is not None, 'Ensure the info dict is set'
        info['__graphql_controller__'] = controller

    # pylint: disable=unused-argument
    async def stop_graphql(scope: Scope, info: Info, request) -> None:
        """Stop the GraphQL controller"""

        logger.debug('Stopping the GraphQL controller')

        assert info is not None, 'Ensure the info dict is set'
        graphql_controller: GraphQLController = info['__graphql_controller__']
        await graphql_controller.shutdown()

    app.startup_handlers.append(start_graphql)
    app.shutdown_handlers.append(stop_graphql)
