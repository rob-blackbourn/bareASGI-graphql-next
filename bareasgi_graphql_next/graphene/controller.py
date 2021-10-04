"""Graphene support"""

from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union
)

from bareasgi import WebSocketRequest, HttpRequest
import graphene
from graphql import ExecutionResult
from graphql.execution import MiddlewareManager
from graphql.subscription.map_async_iterator import MapAsyncIterator

from ..controller import GraphQLControllerBase
from .websocket_handler import GrapheneWebSocketHandler


class GrapheneController(GraphQLControllerBase):
    """Graphene Controller"""

    def __init__(
            self,
            schema: graphene.Schema,
            path_prefix: str,
            middleware: Optional[Union[Tuple, List, MiddlewareManager]],
            ping_interval: float,
            loads: Callable[[str], Any],
            dumps: Callable[[Any], str]
    ) -> None:
        """Create a Graphene controller

        Args:
            schema (graphene.Schema): The Graphene schema
            path_prefix (str): The path prefix.
            middleware (Optional[Union[Tuple, List, MiddlewareManager]): The
                middleware. Defaults to None.
            ping_interval (float): The WebSocket ping interval.
            loads (Callable[[str], Any]): The function to convert a JSON string
                to an object.
            dumps (Callable[[Any], str]): The function to convert an object to a
                JSON string. Defaults to json.dumps.
        """
        super().__init__(path_prefix, middleware, ping_interval, loads, dumps)
        self.schema = schema
        self.ws_subscription_handler = GrapheneWebSocketHandler(schema)

    async def subscribe(
            self,
            request: HttpRequest,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> MapAsyncIterator:
        return await self.schema.subscribe(
            query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=request
        )

    async def query(
            self,
            request: HttpRequest,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> ExecutionResult:
        return await self.schema.execute_async(
            source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=request
        )

    async def handle_websocket_subscription(self, request: WebSocketRequest) -> None:
        """Handle a websocket subscription

        Args:
            request (WebSocketRequest): The request
        """
        await self.ws_subscription_handler(request)
