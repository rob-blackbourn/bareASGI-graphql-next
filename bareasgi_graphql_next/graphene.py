"""Graphene support"""

from typing import Any, Dict, Optional

from baretypes import Scope, Info, RouteMatches, WebSocket
import graphene
import graphql
from graphql.subscription.map_async_iterator import MapAsyncIterator

from .controller import GraphQLControllerBase
from .websocket_instance import GraphQLWebSocketHandlerInstanceBase

class GrapheneWebSocketHandlerInstance(GraphQLWebSocketHandlerInstanceBase):
    """A GraphQL WebSocket handler instance"""

    def __init__(self, schema: graphene.Schema, web_socket: WebSocket, info: Info) -> None:
        super().__init__(web_socket, info)
        self.schema = schema

    async def subscribe(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> MapAsyncIterator:
        return await self.schema.subscribe(
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=self.info
        )

    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> graphql.ExecutionResult:
        return await self.schema.execute(
            source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=self.info
        )

class GrapheneWebSocketHandler:
    """Graphene WebSocket handler"""

    def __init__(self, schema: graphene.Schema):
        """Graphene WebSocket handler
        
        Args:
            schema (graphene.Schema): The schema
        """
        self.schema = schema

    async def __call__(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            web_socket: WebSocket
    ) -> None:
        instance = GrapheneWebSocketHandlerInstance(self.schema, web_socket, info)
        await instance.start(scope['subprotocols'])

class GrapheneController(GraphQLControllerBase):
    """Graphene Controller"""

    def __init__(
            self,
            schema: graphene.Schema,
            path_prefix: str = '',
            middleware=None,
            ping_interval: float = 10
    ) -> None:
        """Create a Graphene controller

        Args:
            schema (graphene.Schema): The Graphene schema
            path_prefix (str, optional): The path prefix. Defaults to ''.
            middleware ([type], optional): The middleware. Defaults to None.
            ping_interval (float, optional): The WebSocket ping interval. Defaults to 10.
        """
        super().__init__(path_prefix, middleware, ping_interval)
        self.schema = schema
        self.ws_subscription_handler = GrapheneWebSocketHandler(schema)

    async def subscribe(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            info: Info
    ) -> MapAsyncIterator:
        return await self.schema.subscribe(
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=info
        )

    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            info: Info
    ) -> graphql.ExecutionResult:
        return await self.schema.execute(
            source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=info
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
