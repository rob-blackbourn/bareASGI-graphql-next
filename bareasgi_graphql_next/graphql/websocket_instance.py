"""GraphQL WebSocket instance"""

from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    cast
)

from bareasgi import WebSocketRequest
import graphql
from graphql import ExecutionResult, GraphQLSchema, MapAsyncIterator

from ..websocket_instance import GraphQLWebSocketHandlerInstanceBase


class GraphQLWebSocketHandlerInstance(GraphQLWebSocketHandlerInstanceBase):
    """A GraphQL WebSocket handler instance"""

    def __init__(
            self,
            schema: GraphQLSchema,
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
        result = await graphql.subscribe(
            schema=self.schema,
            document=graphql.parse(query),
            variable_values=variables,
            operation_name=operation_name,
            context_value=self.request
        )
        return cast(MapAsyncIterator, result)

    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> ExecutionResult:
        return await graphql.graphql(
            schema=self.schema,
            source=graphql.Source(query),
            variable_values=variables,
            operation_name=operation_name,
            context_value=self.request
        )
