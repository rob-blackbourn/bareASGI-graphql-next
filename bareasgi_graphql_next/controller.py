"""GraphQL base controller"""

from abc import ABCMeta, abstractmethod
import asyncio
import io
import json
import logging

from cgi import parse_multipart
from datetime import datetime
from typing import List, Dict, Any, Optional, Mapping
from urllib.parse import parse_qs, urlencode

import graphql
import bareutils.header as header

from graphql import ExecutionResult
from graphql.subscription.map_async_iterator import MapAsyncIterator
from bareasgi import Application
from bareutils import text_reader, text_writer, response_code
from baretypes import (
    Header,
    HttpResponse,
    Scope,
    Info,
    RouteMatches,
    Content,
    WebSocket,
    HttpMiddlewareCallback
)

from .template import make_template
from .utils import (
    cancellable_aiter,
    get_host,
    get_scheme,
    has_subscription,
    wrap_middleware,
    ZeroEvent
)

logger = logging.getLogger(__name__)


def _make_sse_message(val: Optional[ExecutionResult]) -> str:
    if val is None:
        return f'event: ping\ndata: {datetime.utcnow()}\n\n'

    response = {
        'data': val.data,
        'errors': val.errors
    }

    return f'event: message\ndata: {json.dumps(response)}\n\n'


def _make_json_message(val: Optional[ExecutionResult]) -> str:
    if val is None:
        return '\n'

    return json.dumps({
        'data': val.data,
        'errors': val.errors
    }) + '\n'


class GraphQLControllerBase(metaclass=ABCMeta):
    """GraphQL Controller Base"""

    def __init__(
            self,
            path_prefix: str = '',
            middleware=None,
            ping_interval: float = 10
    ) -> None:
        self.path_prefix = path_prefix
        self.middleware = middleware
        self.ping_interval = ping_interval
        self.cancellation_event = asyncio.Event()
        self.subscription_count = ZeroEvent()

    @abstractmethod
    async def subscribe(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            info: Info
    ) -> MapAsyncIterator:
        """Execute a subscription.

        Args:
            query (str): The subscription query.
            variables (Optional[Dict[str, Any]]): Optional variables.
            operation_name (Optional[str]): An optional operation name.
            info (Info): The application info.

        Returns:
            MapAsyncIterator: An asynchronous iterator of the results.
        """

    @abstractmethod
    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            info: Info
    ) -> ExecutionResult:
        """Execute a query

        Args:
            query (str): The subscription query.
            variables (Optional[Dict[str, Any]]): Optional variables.
            operation_name (Optional[str]): An optional operation name.
            info (Info): The application info.

        Returns:
            ExecutionResult: The query results.
        """

    def add_routes(
            self,
            app: Application,
            path_prefix: str = '',
            rest_middleware: Optional[HttpMiddlewareCallback] = None,
            view_middleware: Optional[HttpMiddlewareCallback] = None
    ):
        """Add the routes

        Args:
            app (Application): The ASGI application
            path_prefix (str, optional): The path prefix. Defaults to ''.
            rest_middleware (Optional[HttpMiddlewareCallback], optional): The
                rest middleware. Defaults to None.
            view_middleware (Optional[HttpMiddlewareCallback], optional): The
                view middleware. Defaults to None.
        """
        # Add the REST route
        app.http_router.add(
            {'GET'},
            path_prefix + '/graphql',
            wrap_middleware(rest_middleware, self.handle_graphql)
        )
        app.http_router.add(
            {'POST', 'OPTIONS'},
            path_prefix + '/graphql',
            wrap_middleware(rest_middleware, self.handle_graphql)
        )
        app.http_router.add(
            {'GET'},
            path_prefix + '/subscriptions',
            wrap_middleware(rest_middleware, self.handle_sse_get)
        )
        app.http_router.add(
            {'POST', 'OPTIONS'},
            path_prefix + '/subscriptions',
            wrap_middleware(rest_middleware, self.handle_sse_post)
        )

        # Add the subscription route
        app.ws_router.add(
            path_prefix + '/subscriptions',
            self.handle_websocket_subscription
        )

        # Add Graphiql
        app.http_router.add(
            {'GET'},
            path_prefix + '/graphiql',
            wrap_middleware(view_middleware, self.view_graphiql)
        )

    async def shutdown(self) -> None:
        """Shutdown the service"""
        self.cancellation_event.set()
        await self.subscription_count.wait()

    # pylint: disable=unused-argument
    async def view_graphiql(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            content: Content
    ) -> HttpResponse:
        """Render the Graphiql view


        Args:
            scope (Scope): The ASGI scope
            info (Info): The user info
            matches (RouteMatches): The route matches
            content (Content): The request body

        Returns:
            HttpResponse: [description]
        """

        host = get_host(scope['headers'])
        scheme = get_scheme(scope)
        query_path = f'{scheme}://{host}{self.path_prefix}/graphql'
        ws_scheme = 'ws' if scheme == 'http' else 'wss'
        subscription_path = f'{ws_scheme}://{host}{self.path_prefix}/subscriptions'
        body = make_template(
            host,
            query_path,
            subscription_path
        )
        headers = [
            (b'content-type', b'text/html'),
            (b'content-length', str(len(body)).encode())
        ]
        return response_code.OK, headers, text_writer(body)

    @abstractmethod
    async def handle_websocket_subscription(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            web_socket: WebSocket
    ) -> None:
        """Handle a websocket subscription

        Args:
            scope (Scope): The ASGI scope
            info (Info): The application info
            matches (RouteMatches): The route matches
            web_socket (WebSocket): The web socket to interact with
        """

    @classmethod
    async def _get_query_document(
            cls,
            headers: List[Header],
            content: Content
    ) -> Mapping[str, Any]:
        content_type, parameters = header.content_type(headers)

        if content_type == b'application/graphql':
            return {'query': await text_reader(content)}
        elif content_type in (b'application/json', b'text/plain'):
            return json.loads(await text_reader(content))
        elif content_type == b'application/x-www-form-urlencoded':
            body = parse_qs(await text_reader(content))
            return {name: value[0] for name, value in body.items()}
        elif content_type == b'multipart/form-data':
            return {
                name: value[0]
                for name, value in parse_multipart(
                    io.StringIO(await text_reader(content)),
                    {key.decode('utf-8'): val for key,
                     val in parameters.items()}
                ).items()
            }
        else:
            raise RuntimeError('Content type not supported')

    # pylint: disable=unused-argument
    async def handle_graphql(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            content: Content
    ) -> HttpResponse:
        """A request handler for graphql queries

        Args:
            scope (Scope): The ASGI scope
            info (Info): The application info object
            matches (RouteMatches): The route matches
            content (Content): The request body

        Returns:
            HttpResponse: The HTTP response to the query request
        """

        try:
            body = await self._get_query_document(scope['headers'], content)

            query: str = body['query']
            variables: Optional[Dict[str, Any]] = body.get('variables')
            operation_name: Optional[str] = body.get('operationName')

            query_document = graphql.parse(query)

            if has_subscription(query_document):
                method = header.find(b'allow', scope['headers'], b'GET')
                if method == b'GET':
                    # Handle a subscription by returning 201 (Created) with
                    # the url location of the subscription.
                    scheme = scope['scheme']
                    host = header.find(
                        b'host', scope['headers'], b'localhost').decode()
                    path = self.path_prefix + '/subscriptions'
                    query_string = urlencode(
                        {
                            name.encode('utf-8'): json.dumps(value).encode('utf-8')
                            for name, value in body.items()
                        }
                    )
                    location = f'{scheme}://{host}{path}'
                    location += f'?{query_string}'
                    headers = [
                        (b'access-control-expose-headers', b'location'),
                        (b'location', location.encode('ascii'))
                    ]
                    return response_code.CREATED, headers
                else:
                    return await self._handle_sse(scope, info, body)
            else:
                # Handle a query
                result = await self.query(
                    query,
                    variables,
                    operation_name,
                    info
                )

                response: Dict[str, Any] = {'data': result.data}
                if result.errors:
                    response['errors'] = [
                        error.formatted for error in result.errors]

                text = json.dumps(response)
                headers = [
                    (b'content-type', b'application/json'),
                    (b'content-length', str(len(text)).encode())
                ]

                return 200, headers, text_writer(text)

        # pylint: disable=bare-except
        except:
            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return response_code.INTERNAL_SERVER_ERROR, headers, text_writer(text)

    async def handle_sse_get(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            content: Content
    ) -> HttpResponse:
        """Handle a server sent event style direct subscription

        Args:
            scope (Scope): The ASGI scope
            info (Info): The application info object
            matches (RouteMatches): The route matches
            content (Content): The request body

        Returns:
            HttpResponse: The streaming response
        """

        logger.debug(
            'SSE received GET subscription request: http_version=%s',
            scope['http_version']
        )

        body = {
            name.decode('utf-8'): json.loads(value[0].decode('utf-8'))
            for name, value in parse_qs(scope['query_string']).items()
        }

        return await self._handle_sse(scope, info, body)

    async def handle_sse_post(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            content: Content
    ) -> HttpResponse:
        """Handle a server sent event style direct subscription

        Args:
            scope (Scope): The ASGI scope
            info (Info): The application info object
            matches (RouteMatches): The route matches
            content (Content): The request body

        Returns:
            HttpResponse: A stream response
        """

        logger.debug(
            'SSE received POST subscription request: http_version=%s',
            scope['http_version']
        )

        content = await text_reader(content)
        body = json.loads(content)

        return await self._handle_sse(scope, info, body)

    async def _handle_sse(
            self,
            scope: Scope,
            info: Info,
            body: Mapping[str, Any]
    ) -> HttpResponse:
        """Handle a server sent event style direct subscription"""

        accept = header.find(b'accept', scope['headers'], b'text/event-stream')
        content_type = b'application/stream+json' if accept == b'application/json' else accept

        result = await self.subscribe(
            body['query'],
            body.get('variables'),
            body.get('operationName'),
            info
        )

        # Make an async iterator for the subscription results.

        async def send_events(zero_event: ZeroEvent):
            logger.debug('Started SSE subscription')

            try:
                zero_event.increment()

                async for val in cancellable_aiter(
                        result,
                        self.cancellation_event,
                        timeout=self.ping_interval
                ):
                    if content_type == b'text/event-stream':
                        yield _make_sse_message(val).encode('utf-8')
                        # Give the ASGI server a nudge.
                        yield b':\n\n'
                    else:
                        yield _make_json_message(val).encode('utf-8')
                        yield b'\n'

            except asyncio.CancelledError:
                logger.debug("Cancelled SSE subscription")
            finally:
                zero_event.decrement()

            logger.debug('Stopped SSE subscription')

        headers = [
            (b'cache-control', b'no-cache'),
            # (b'content-type', b'text/event-stream'),
            (b'content-type', content_type),
            (b'connection', b'keep-alive')
        ]

        return response_code.OK, headers, send_events(self.subscription_count)
