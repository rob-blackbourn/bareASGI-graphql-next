"""Graphene support"""

from bareasgi import WebSocketRequest
import graphene

from .websocket_instance import GrapheneWebSocketHandlerInstance


class GrapheneWebSocketHandler:
    """Graphene WebSocket handler"""

    def __init__(self, schema: graphene.Schema):
        """Graphene WebSocket handler

        Args:
            schema (graphene.Schema): The schema
        """
        self.schema = schema

    async def __call__(self, request: WebSocketRequest) -> None:
        instance = GrapheneWebSocketHandlerInstance(self.schema, request)
        await instance.start(request.scope['subprotocols'])
