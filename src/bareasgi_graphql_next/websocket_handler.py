from bareasgi import (
    Scope,
    Info,
    RouteMatches,
    WebSocket
)
import graphql

from .websocket_instance import GraphQLWebSocketHandlerInstance


class GraphQLWebSocketHandler:

    def __init__(self, schema: graphql.GraphQLSchema):
        self.schema = schema

    async def __call__(self, scope: Scope, info: Info, matches: RouteMatches, web_socket: WebSocket) -> None:
        instance = GraphQLWebSocketHandlerInstance(self.schema, web_socket, info)
        await instance.start(scope['subprotocols'])
