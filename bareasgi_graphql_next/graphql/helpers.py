"""Helpers for installing the graphql middleware"""

import json
import logging
from typing import Any, Callable, Optional

from bareasgi import Application, LifespanRequest, HttpMiddlewareCallback
from graphql import GraphQLSchema

from .controller import GraphQLController

logger = logging.getLogger(__name__)

GRAPHQL_INFO_KEY = '__bareasgi_graphql_next.graphql__'


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

    async def start_graphql(request: LifespanRequest) -> None:
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
        request.info[GRAPHQL_INFO_KEY] = controller

    async def stop_graphql(request: LifespanRequest) -> None:
        """Stop the GraphQL controller"""

        logger.debug('Stopping the GraphQL controller')

        graphql_controller: GraphQLController = request.info[GRAPHQL_INFO_KEY]
        await graphql_controller.shutdown()

    app.startup_handlers.append(start_graphql)
    app.shutdown_handlers.append(stop_graphql)
