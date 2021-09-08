"""
GraphQL controller
"""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
    cast
)

import graphql

from graphql import GraphQLSchema, ExecutionResult
from graphql.execution import MiddlewareManager
from graphql.subscription.map_async_iterator import MapAsyncIterator
from baretypes import (
    Scope,
    Info,
    RouteMatches,
    WebSocket
)

from ..controller import GraphQLControllerBase
from .websocket_handler import GraphQLWebSocketHandler


class GraphQLController(GraphQLControllerBase):
    """GraphQL Controller"""

    def __init__(
            self,
            schema: GraphQLSchema,
            path_prefix: str,
            middleware: Optional[Union[Tuple, List, MiddlewareManager]],
            ping_interval: float,
            loads: Callable[[str], Any],
            dumps: Callable[[Any], str]
    ) -> None:
        """Create a GraphQL controller

        Args:
            schema (GraphQLSchema): The Graphql schema
            path_prefix (str): The path prefix.
            middleware (Optional[Union[Tuple, List, MiddlewareManager]): The
                middleware. Defaults to None.
            ping_interval (float): The WebSocket ping interval.
            loads (Callable[[str], Any]): The function to convert a JSON string
                to an object.
            dumps (Callable[[Any], str]): The function to convert an object to a
                JSON string.
        """
        super().__init__(path_prefix, middleware, ping_interval, loads, dumps)
        self.schema = schema
        self.ws_subscription_handler = GraphQLWebSocketHandler(schema)

    async def subscribe(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            scope: Scope,
            info: Info
    ) -> MapAsyncIterator:
        result = await graphql.subscribe(
            schema=self.schema,
            document=graphql.parse(query),
            variable_values=variables,
            operation_name=operation_name,
            context_value={'scope': scope, 'info': info}
        )
        return cast(MapAsyncIterator, result)

    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            scope: Scope,
            info: Info
    ) -> ExecutionResult:
        return await graphql.graphql(
            schema=self.schema,
            source=graphql.Source(query),  # source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value={'scope': scope, 'info': info},
            middleware=self.middleware
        )

    async def handle_websocket_subscription(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            web_socket: WebSocket
    ) -> None:
        """Handle a websocket subscription

        Args:
            scope (Scope): The ASGI scope
            info (Info): The application info
            matches (RouteMatches): The route matches
            web_socket (WebSocket): The web socket to interact with
        """
        await self.ws_subscription_handler(scope, info, matches, web_socket)
