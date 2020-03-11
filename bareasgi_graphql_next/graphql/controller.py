"""
GraphQL controller
"""

from typing import Dict, Any, Optional, cast

import graphql

from graphql import GraphQLSchema, ExecutionResult
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
            path_prefix: str = '',
            middleware=None,
            ping_interval: float = 10
    ) -> None:
        """Create a GraphQL controller

        Args:
            schema (GraphQLSchema): The Graphql schema
            path_prefix (str, optional): The path prefix. Defaults to ''.
            middleware ([type], optional): The middleware. Defaults to None.
            ping_interval (float, optional): The WebSocket ping interval. Defaults to 10.
        """
        super().__init__(path_prefix, middleware, ping_interval)
        self.schema = schema
        self.ws_subscription_handler = GraphQLWebSocketHandler(schema)

    async def subscribe(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            info: Info
    ) -> MapAsyncIterator:
        result = await graphql.subscribe(
            schema=self.schema,
            document=graphql.parse(query),
            variable_values=variables,
            operation_name=operation_name,
            context_value=info
        )
        return cast(MapAsyncIterator, result)

    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            info: Info
    ) -> ExecutionResult:
        return await graphql.graphql(
            schema=self.schema,
            source=graphql.Source(query),  # source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=info,
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
