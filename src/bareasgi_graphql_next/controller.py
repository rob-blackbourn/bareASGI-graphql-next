import asyncio
from cgi import parse_multipart
# noinspection PyPackageRequirements
import graphql
from graphql import OperationType, GraphQLSchema
import io
import json
from typing import List, AsyncIterator, MutableMapping
from urllib.parse import parse_qs
import uuid
from bareasgi import Application
from bareasgi.utils import aiter, anext
import bareutils.header as header
from bareutils import text_reader, text_writer, response_code
from baretypes import (Header, HttpResponse, Scope, Info, RouteMatches, Content, WebSocket)
from bareasgi.middleware import mw

from .template import make_template
from .websocket_handler import GraphQLWebSocketHandler
from .utils import parse_header


class GraphQLController:

    def __init__(self, schema: GraphQLSchema, path_prefix: str = '', middleware=None):
        self.schema = schema
        self.path_prefix = path_prefix
        self.middleware = middleware
        self.ws_subscription_handler = GraphQLWebSocketHandler(schema)
        self.sse_subscriptions: MutableMapping[str, AsyncIterator] = dict()
        self.cancellation_event = asyncio.Event()

    def shutdown(self) -> None:
        self.cancellation_event.set()

    # noinspection PyUnusedLocal
    async def view_graphiql(self, scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:
        host, port = scope['server']
        body = make_template(f'{host}:{port}', self.path_prefix + '/graphql', self.path_prefix + '/subscriptions')
        headers = [
            (b'content-type', b'text/html'),
            (b'content-length', str(len(body)).encode())
        ]
        return response_code.OK, headers, text_writer(body)

    async def handle_subscription(self, scope: Scope, info: Info, matches: RouteMatches, web_socket: WebSocket) -> None:
        await self.ws_subscription_handler(scope, info, matches, web_socket)

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
            return parse_multipart(io.StringIO(await text_reader(content)), parameters[b"boundary"])
        else:
            raise RuntimeError('Content type not supported')

    # noinspection PyUnusedLocal
    async def handle_graphql(self, scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:

        # noinspection PyBroadException
        try:
            query_document = await self._get_query_document(scope['headers'], content)

            query = query_document['query']
            variable_values = query_document.get('variables')
            operation_name = query_document.get('operationName')

            parsed_query = graphql.parse(query)

            if any(definition.operation is OperationType.SUBSCRIPTION for definition in parsed_query.definitions):
                result = await graphql.subscribe(
                    schema=self.schema,
                    document=parsed_query,
                    variable_values=variable_values,
                    operation_name=operation_name,
                    context_value=info
                )
            else:
                result = await graphql.graphql(
                    schema=self.schema,
                    source=graphql.Source(query),  # source=query,
                    variable_values=variable_values,
                    operation_name=operation_name,
                    context_value=info,
                    middleware=self.middleware
                )

            if not isinstance(result, AsyncIterator):
                response = {'data': result.data}
                if result.errors:
                    response['errors'] = [error.formatted for error in result.errors]

                text = json.dumps(response)
                headers = [
                    (b'content-type', b'application/json'),
                    (b'content-length', str(len(text)).encode())
                ]

                return 200, headers, text_writer(text)
            else:
                token = str(uuid.uuid4())
                self.sse_subscriptions[token] = result
                host = header.find(b'host', scope['headers']).decode('utf-8')
                location = f'{scope["scheme"]}://{host}{self.path_prefix}/sse-subscription/{token}'
                headers = [
                    (b'access-control-expose-headers', b'location'),
                    (b'location', location.encode('ascii'))
                ]
                return response_code.CREATED, headers

        except:
            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return response_code.INTERNAL_SERVER_ERROR, headers, text_writer(text)

    async def handle_sse(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            content: Content
    ) -> HttpResponse:
        token = matches['token']
        result = self.sse_subscriptions[token]

        async def send_events():
            try:
                cancellation_task = self.cancellation_event.wait()
                result_iter = result.__aiter__()
                while not self.cancellation_event.is_set():
                    done, pending = await asyncio.wait(
                        [cancellation_task, result_iter.__anext__()],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    for done_task in done:
                        if done_task == cancellation_task:
                            for pending_task in pending:
                                pending_task.cancel()
                            break
                        else:
                            val = done_task.result()
                            text = json.dumps(val)
                            yield f'data: {text}\n\n\n'.encode('utf-8')

            except asyncio.CancelledError as error:
                pass

        headers = [
            (b'cache-control', b'no-cache'),
            (b'content-type', b'text/event-stream'),
            (b'connection', b'keep-alive')
        ]

        return response_code.OK, headers, send_events()


def add_graphql_next(
        app: Application,
        schema: GraphQLSchema,
        path_prefix: str = '',
        rest_middleware=None,
        view_middleware=None,
        graphql_middleware=None
) -> GraphQLController:
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
    app.http_router.add(
        {'GET'},
        path_prefix + '/sse-subscription/{token}',
        controller.handle_sse if rest_middleware is None else mw(rest_middleware, handler=controller.handle_sse)
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

    return controller
