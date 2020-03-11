"""Graphene support"""

from baretypes import Scope, Info, RouteMatches, WebSocket
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

    async def __call__(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            web_socket: WebSocket
    ) -> None:
        instance = GrapheneWebSocketHandlerInstance(self.schema, web_socket, info)
        await instance.start(scope['subprotocols'])
