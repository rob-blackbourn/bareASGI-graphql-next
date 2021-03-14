"""
WebSocket handler
"""

from baretypes import (
    Scope,
    Info,
    RouteMatches,
    WebSocket
)
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
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            web_socket: WebSocket
    ) -> None:
        instance = GraphQLWebSocketHandlerInstance(
            self.schema,
            web_socket,
            scope,
            info
        )
        await instance.start(scope['subprotocols'])
