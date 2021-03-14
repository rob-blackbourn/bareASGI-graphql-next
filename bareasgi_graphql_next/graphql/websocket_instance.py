"""
GraphQL WebSocket instance
"""

from typing import (
    Any,
    Dict,
    Optional,
    cast
)

from baretypes import Info, Scope, WebSocket
import graphql
from graphql import ExecutionResult, GraphQLSchema
from graphql.subscription.map_async_iterator import MapAsyncIterator

from ..websocket_instance import GraphQLWebSocketHandlerInstanceBase


class GraphQLWebSocketHandlerInstance(GraphQLWebSocketHandlerInstanceBase):
    """A GraphQL WebSocket handler instance"""

    def __init__(
            self,
            schema: GraphQLSchema,
            web_socket: WebSocket,
            scope: Scope,
            info: Info
    ) -> None:
        super().__init__(web_socket, scope, info)
        self.schema = schema

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
            context_value={'scope': self.scope, 'info': self.info}
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
            source=graphql.Source(query),  # source=query,
            variable_values=variables,
            operation_name=operation_name,
            context_value={'scope': self.scope, 'info': self.info}
        )
