"""Graphene support"""

from typing import Any, Dict, Optional

from bareasgi import WebSocketRequest
import graphene
import graphql
from graphql.subscription.map_async_iterator import MapAsyncIterator

from ..websocket_instance import GraphQLWebSocketHandlerInstanceBase


class GrapheneWebSocketHandlerInstance(GraphQLWebSocketHandlerInstanceBase):
    """A GraphQL WebSocket handler instance"""

    def __init__(
            self,
            schema: graphene.Schema,
            request: WebSocketRequest
    ) -> None:
        super().__init__(request.web_socket)
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
    ) -> graphql.ExecutionResult:
        return await self.schema.execute_async(
            source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value=self.request
        )
