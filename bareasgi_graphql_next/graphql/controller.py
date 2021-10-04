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
from bareasgi import HttpRequest, WebSocketRequest

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
            request: HttpRequest,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> MapAsyncIterator:
        result = await graphql.subscribe(
            schema=self.schema,
            document=graphql.parse(query),
            variable_values=variables,
            operation_name=operation_name,
            context_value=request
        )
        return cast(MapAsyncIterator, result)

    async def query(
            self,
            request: HttpRequest,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> ExecutionResult:
        return await graphql.graphql(
            schema=self.schema,
            source=graphql.Source(query),  # source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=request,
            middleware=self.middleware
        )

    async def handle_websocket_subscription(self, request: WebSocketRequest) -> None:
        """Handle a websocket subscription

        Args:
            request (WebSocketRequest): The request
        """
        await self.ws_subscription_handler(request)
