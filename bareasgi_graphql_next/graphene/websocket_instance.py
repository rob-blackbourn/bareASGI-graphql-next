"""Graphene WebSocket instance"""

from typing import Any, Callable, Dict, Optional

from bareasgi import WebSocketRequest
from graphene import Schema
from graphql import ExecutionResult, MapAsyncIterator

from ..websocket_instance import GraphQLWebSocketHandlerInstanceBase


class GrapheneWebSocketHandlerInstance(GraphQLWebSocketHandlerInstanceBase):
    """A GraphQL WebSocket handler instance"""

    def __init__(
            self,
            schema: Schema,
            request: WebSocketRequest,
            dumps: Callable[[Any], str]
    ) -> None:
        super().__init__(request.web_socket, dumps)
        self.schema = schema
        self.request = request

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
            context_value=self.request
        )

    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> ExecutionResult:
        return await self.schema.execute_async(
            source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=self.request
        )
