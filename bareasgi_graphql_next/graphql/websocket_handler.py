"""GraphQL WebSocket handler"""

from typing import Any, Callable
from bareasgi import WebSocketRequest
import graphql

from .websocket_instance import GraphQLWebSocketHandlerInstance


class GraphQLWebSocketHandler:
    """GraphQL WebSocket handler"""

    def __init__(self, schema: graphql.GraphQLSchema):
        """GraphQL WebSocket handler

        Args:
            schema (graphql.GraphQLSchema): The schema
        """
        self.schema = schema

    async def __call__(
            self,
            request: WebSocketRequest,
            dumps: Callable[[Any], str]
    ) -> None:
        instance = GraphQLWebSocketHandlerInstance(
            self.schema,
            request,
            dumps
        )
        await instance.start(request.scope['subprotocols'])
