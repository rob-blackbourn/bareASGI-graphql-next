from cgi import parse_multipart
# noinspection PyPackageRequirements
from graphql import graphql, GraphQLSchema
import io
from typing import List
from urllib.parse import parse_qs
import json
from bareasgi import (
    Application,
    Scope,
    Info,
    RouteMatches,
    Content,
    HttpResponse,
    WebSocket,
    text_writer,
    text_reader
)
from bareasgi.types import Header
from bareasgi.middleware import mw

from .template import make_template
from .websocket_handler import GraphQLWebSocketHandler
from .utils import parse_header


class GraphQLController:

    def __init__(self, schema: GraphQLSchema, path_prefix: str = '', middleware=None):
        self.schema = schema
        self.path_prefix = path_prefix
        self.middleware = middleware
        self.subscription_handler = GraphQLWebSocketHandler(schema)

    # noinspection PyUnusedLocal
    async def view_graphiql(self, scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:
        host, port = scope['server']
        body = make_template(f'{host}:{port}', self.path_prefix + '/graphql', self.path_prefix + '/subscriptions')
        headers = [
            (b'content-type', b'text/html'),
            (b'content-length', str(len(body)).encode())
        ]
        return 200, headers, text_writer(body)

    async def handle_subscription(self, scope: Scope, info: Info, matches: RouteMatches, web_socket: WebSocket) -> None:
        await self.subscription_handler(scope, info, matches, web_socket)

    @classmethod
    async def _get_query_document(cls, headers: List[Header], content: Content):
        content_type = next((v for k, v in headers if k == b'content-type'), None)
        content_type, parameters = parse_header(content_type)

        if content_type == b'application/graphql':
            return {'query': await text_reader(content)}
        elif content_type in (b'application/json', b'text/plain'):
            return json.loads(await text_reader(content))
        elif content_type == b'application/x-www-form-urlencoded':
            return parse_qs(await text_reader(content))
        elif content_type == b'multipart/form-data':
            return parse_multipart(io.StringIO(await text_reader(content)), parameters["boundary"])
        else:
            raise RuntimeError('Content type not supported')

    # noinspection PyUnusedLocal
    async def handle_graphql(self, scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:

        # noinspection PyBroadException
        try:
            query_document = await self._get_query_document(scope['headers'], content)

            result = await graphql(
                schema=self.schema,
                source=query_document['query'],
                variable_values=query_document.get('variables'),
                operation_name=query_document.get('operationName'),
                context_value=info,
                middleware=self.middleware
            )

            response = {'data': result.data}
            if result.errors:
                response['errors'] = [error.formatted for error in result.errors]

            text = json.dumps(response)
            headers = [
                (b'content-type', b'application/json'),
                (b'content-length', str(len(text)).encode())
            ]

            return 200, headers, text_writer(text)

        except:
            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return 500, headers, text_writer(text)


def add_graphql_next(
        app: Application,
        schema: GraphQLSchema,
        path_prefix: str = '',
        rest_middleware=None,
        view_middleware=None,
        graphql_middleware=None
) -> None:
    controller = GraphQLController(schema, path_prefix, graphql_middleware)

    # Add the REST route
    app.http_router.add(
        {'GET'},
        path_prefix + '/graphql',
        controller.handle_graphql if rest_middleware is None else mw(rest_middleware, handler=controller.handle_graphql)
    )
    app.http_router.add(
        {'POST', 'OPTION'},
        path_prefix + '/graphql',
        controller.handle_graphql if rest_middleware is None else mw(rest_middleware, handler=controller.handle_graphql)
    )

    # Add the subscription route
    app.ws_router.add(
        path_prefix + '/subscriptions',
        controller.handle_subscription
    )

    # Add Graphiql
    app.http_router.add(
        {'GET'},
        path_prefix + '/graphiql',
        controller.view_graphiql if view_middleware is None else mw(view_middleware, handler=controller.view_graphiql)
    )
