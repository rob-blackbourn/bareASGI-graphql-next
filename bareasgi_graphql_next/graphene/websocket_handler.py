"""Graphene support"""

from bareasgi import WebSocketRequest
from graphene import Schema

from .websocket_instance import GrapheneWebSocketHandlerInstance


class GrapheneWebSocketHandler:
    """Graphene WebSocket handler"""

    def __init__(self, schema: Schema):
        """Graphene WebSocket handler

        Args:
            schema (Schema): The schema
        """
        self.schema = schema

    async def __call__(self, request: WebSocketRequest) -> None:
        instance = GrapheneWebSocketHandlerInstance(self.schema, request)
        await instance.start(request.scope['subprotocols'])
