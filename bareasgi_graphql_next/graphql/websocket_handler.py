"""
WebSocket handler
"""

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

    async def __call__(self, request: WebSocketRequest) -> None:
        instance = GraphQLWebSocketHandlerInstance(self.schema, request)
        await instance.start(request.scope['subprotocols'])
