import asyncio
from base64 import b64encode
from cgi import parse_multipart
from dataclasses import dataclass, field
from datetime import datetime, timedelta
# noinspection PyPackageRequirements
import graphql
from graphql import OperationType, GraphQLSchema
from graphql.subscription.map_async_iterator import MapAsyncIterator
import io
import json
import logging
from typing import List, MutableMapping
from urllib.parse import parse_qs
import uuid
from bareasgi import Application
import bareutils.header as header
from bareutils import text_reader, text_writer, response_code
from baretypes import (Header, HttpResponse, Scope, Info, RouteMatches, Content, WebSocket)
from bareasgi.middleware import mw

from .template import make_template
from .websocket_handler import GraphQLWebSocketHandler
from .utils import parse_header, cancellable_aiter

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    result: MapAsyncIterator
    created: datetime = field(default_factory=datetime.utcnow)


def _is_http_2(scope: Scope) -> bool:
    return scope['http_version'] in ('2', '2.0')


def _get_host(scope: Scope) -> bytes:
    if _is_http_2(scope):
        return header.find(b':authority', scope['headers'])
    else:
        return header.find(b'host', scope['headers'])


def _is_subscription(definition: graphql.DefinitionNode) -> bool:
    return isinstance(
        definition,
        graphql.OperationDefinitionNode
    ) and definition.operation is OperationType.SUBSCRIPTION


def _has_subscription(document: graphql.DocumentNode) -> bool:
    return any(_is_subscription(definition) for definition in document.definitions)


class GraphQLController:

    def __init__(
            self,
            schema: GraphQLSchema,
            path_prefix: str = '',
            middleware=None,
            subscription_expiry: float = 60,
            ping_interval: float = 10
    ) -> None:
        self.schema = schema
        self.path_prefix = path_prefix
        self.middleware = middleware
        self.subscription_expiry = subscription_expiry
        self.ping_interval = ping_interval
        self.ws_subscription_handler = GraphQLWebSocketHandler(schema)
        self.sse_subscriptions: MutableMapping[str, Subscription] = dict()
        self.cancellation_event = asyncio.Event()

    def shutdown(self) -> None:
        self.cancellation_event.set()

    # noinspection PyUnusedLocal
    async def view_graphiql(self, scope: Scope, info: Info, matches: RouteMatches, content: Content) -> HttpResponse:
        host = _get_host(scope).decode('ascii')
        body = make_template(f'{host}', self.path_prefix + '/graphql', self.path_prefix + '/subscriptions')
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
        """A request handler for graphql queries"""

        try:
            await self._reap_subscriptions()

            body = await self._get_query_document(scope['headers'], content)

            query_text = body['query']
            variable_values = body.get('variables')
            operation_name = body.get('operationName')

            query_document = graphql.parse(query_text)

            # noinspection PyUnresolvedReferences
            if _has_subscription(query_document):
                result = await graphql.subscribe(
                    schema=self.schema,
                    document=query_document,
                    variable_values=variable_values,
                    operation_name=operation_name,
                    context_value=info
                )
            else:
                result = await graphql.graphql(
                    schema=self.schema,
                    source=graphql.Source(query_text),  # source=query,
                    variable_values=variable_values,
                    operation_name=operation_name,
                    context_value=info,
                    middleware=self.middleware
                )

            if not isinstance(result, MapAsyncIterator):
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
                self.sse_subscriptions[token] = Subscription(result)
                host = _get_host(scope).decode('utf-8')
                location = f'{scope["scheme"]}://{host}{self.path_prefix}/sse-subscription/{token}'
                headers = [
                    (b'access-control-expose-headers', b'location'),
                    (b'location', location.encode('ascii'))
                ]
                return response_code.CREATED, headers

        # noinspection PyBroadException
        except:
            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return response_code.INTERNAL_SERVER_ERROR, headers, text_writer(text)

    # noinspection PyUnusedLocal
    async def handle_sse(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            content: Content
    ) -> HttpResponse:
        """Handled a server sent event style subscription"""

        # The token for the subscription is given in the url.
        token = matches['token']
        subscription = self.sse_subscriptions[token]
        del self.sse_subscriptions[token]

        logger.debug('SSE received subscription request: token="%s", htto_version=%s', token, scope['http_version'])

        # Make an async iterator for the subscription results.
        async def send_events():
            logger.debug('SSE sending events: token="%s"', token)

            try:
                async for val in cancellable_aiter(
                        subscription.result,
                        self.cancellation_event,
                        timeout=self.ping_interval
                ):
                    if val is None:
                        message = f'event: ping\ndata: {datetime.utcnow()}\n\n'.encode('utf-8')
                    else:
                        text = json.dumps(val)
                        buf = text.encode('utf-8')
                        data = b64encode(buf)
                        message = f'event: message\ndata: {text}\n\n'.encode('utf-8')

                    logger.debug('SSE sending: %s', message)
                    yield message
                    # Give the ASGI server a nudge.
                    yield ':\n\n'.encode('utf-8')
            except asyncio.CancelledError:
                logger.debug("SSE task cancelled for token '%s'", token)

            logger.debug('SSE Stopped subscription for token "%s"', token)

        headers = [
            (b'cache-control', b'no-cache'),
            (b'content-type', b'text/event-stream'),
            (b'connection', b'keep-alive')
        ]

        return response_code.OK, headers, send_events()

    async def _reap_subscriptions(self) -> None:
        """Remove subscriptions that were never opened"""
        expiry = datetime.utcnow() - timedelta(seconds=self.subscription_expiry)
        tokens = {
            token: subscription.result
            for token, subscription in self.sse_subscriptions.items()
            if subscription.created < expiry
        }
        for token, result in tokens.items():
            await result.aclose()
            del self.sse_subscriptions[token]


def add_graphql_next(
        app: Application,
        schema: GraphQLSchema,
        path_prefix: str = '',
        rest_middleware=None,
        view_middleware=None,
        graphql_middleware=None,
        subscription_expiry: float = 60,
        ping_interval: float = 10
) -> GraphQLController:
    """Add graphql support to an bareASGI application.

    :param app: The bareASGI application.
    :param schema: The GraphQL schema to use.
    :param path_prefix: An optional path prefix from which to provide enedpoints.
    :param rest_middleware: Middleware for the rest end points.
    :param view_middleware: Middleware from the GraphiQL end point.
    :param graphql_middleware: Middleware for graphql-core-next.
    :param subscription_expiry: The time to wait before abandoning an unused subscription.
    :return: Returns the constructed controller.
    """
    controller = GraphQLController(schema, path_prefix, graphql_middleware, subscription_expiry, ping_interval)

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
