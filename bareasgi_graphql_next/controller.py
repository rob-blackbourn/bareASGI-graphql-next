"""GraphQL base controller"""

from abc import ABCMeta, abstractmethod
import asyncio
from cgi import parse_multipart
from datetime import datetime
from functools import partial
import io
import logging
from typing import (
    Any,
    AsyncIterable,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Union,
    cast
)
from urllib.parse import parse_qs, urlencode

import graphql
from graphql import ExecutionResult
from graphql.error.graphql_error import GraphQLError
from graphql.execution import MiddlewareManager
from graphql.subscription.map_async_iterator import MapAsyncIterator
from bareasgi import Application
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
from bareutils import text_reader, text_writer, response_code
import bareutils.header as header

from .template import make_template
from .utils import (
    cancellable_aiter,
    get_host,
    get_scheme,
    has_subscription,
    wrap_middleware,
    ZeroEvent
)

LOGGER = logging.getLogger(__name__)


def _encode_sse(
        dumps: Callable[[Any], str],
        execution_result: Optional[ExecutionResult]
) -> bytes:
    if execution_result is None:
        payload = f'event: ping\ndata: {datetime.utcnow()}\n\n'
    else:
        response = {
            'data': execution_result.data,
            'errors': [
                error.formatted
                for error in execution_result.errors
            ] if execution_result.errors else None
        }

        payload = f'event: message\ndata: {dumps(response)}\n\n'

    return payload.encode('utf-8')


def _encode_json(
        dumps: Callable[[Any], str],
        execution_result: Optional[ExecutionResult]
) -> bytes:
    if execution_result is None:
        return b'\n'

    payload = dumps({
        'data': execution_result.data,
        'errors': [
            error.formatted
            for error in execution_result.errors
        ] if execution_result.errors else None
    }) + '\n'

    return payload.encode('utf-8')


class GraphQLControllerBase(metaclass=ABCMeta):
    """GraphQL Controller Base"""

    def __init__(
            self,
            path_prefix: str,
            middleware: Optional[Union[Tuple, List, MiddlewareManager]],
            ping_interval: float,
            loads: Callable[[str], Any],
            dumps: Callable[[Any], str]
    ) -> None:
        self.path_prefix = path_prefix
        self.middleware = middleware
        self.ping_interval = ping_interval
        self.loads = loads
        self.dumps = dumps
        self.cancellation_event = asyncio.Event()
        self.subscription_count = ZeroEvent()

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
            wrap_middleware(rest_middleware, self.handle_subscription_get)
        )
        app.http_router.add(
            {'POST', 'OPTIONS'},
            path_prefix + '/subscriptions',
            wrap_middleware(rest_middleware, self.handle_subscription_post)
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

            if not has_subscription(query_document):
                return await self._handle_query_or_mutation(
                    scope,
                    info,
                    query,
                    variables,
                    operation_name
                )

            # The subscription method is determined by the `allow` header.
            allow = header.find(b'allow', scope['headers'], b'GET')
            if allow == b'GET':
                return self._handle_subscription_redirect(scope, body)

            return await self._handle_streaming_subscription(
                scope,
                info,
                query,
                variables,
                operation_name
            )

        # pylint: disable=bare-except
        except:
            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return response_code.INTERNAL_SERVER_ERROR, headers, text_writer(text)

    async def handle_subscription_get(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            content: Content
    ) -> HttpResponse:
        """Handle a streaming subscription

        Args:
            scope (Scope): The ASGI scope
            info (Info): The application info object
            matches (RouteMatches): The route matches
            content (Content): The request body

        Returns:
            HttpResponse: The streaming response
        """

        LOGGER.debug(
            "Received GET streaming subscription request: http_version='%s'.",
            scope['http_version']
        )

        body = {
            name.decode('utf-8'): self.loads(value[0].decode('utf-8'))
            for name, value in cast(
                Dict[bytes, List[bytes]],
                parse_qs(scope['query_string'])
            ).items()
        }

        query: str = body['query']
        variables: Optional[Dict[str, Any]] = body.get('variables')
        operation_name: Optional[str] = body.get('operationName')

        return await self._handle_streaming_subscription(
            scope,
            info,
            query,
            variables,
            operation_name
        )

    async def handle_subscription_post(
            self,
            scope: Scope,
            info: Info,
            matches: RouteMatches,
            content: Content
    ) -> HttpResponse:
        """Handle a streaming subscription

        Args:
            scope (Scope): The ASGI scope
            info (Info): The application info object
            matches (RouteMatches): The route matches
            content (Content): The request body

        Returns:
            HttpResponse: A stream response
        """

        LOGGER.debug(
            "Received POST streaming subscription request: http_version='%s'.",
            scope['http_version']
        )

        text = await text_reader(content)
        body = self.loads(text)

        query: str = body['query']
        variables: Optional[Dict[str, Any]] = body.get('variables')
        operation_name: Optional[str] = body.get('operationName')

        return await self._handle_streaming_subscription(
            scope,
            info,
            query,
            variables,
            operation_name
        )

    async def _get_query_document(
            self,
            headers: List[Header],
            content: Content
    ) -> Mapping[str, Any]:
        content_type = header.content_type(headers)
        if content_type is None:
            raise ValueError('Content type not specified')
        media_type, parameters = content_type

        if media_type == b'application/graphql':
            return {'query': await text_reader(content)}
        elif media_type in (b'application/json', b'text/plain'):
            return self.loads(await text_reader(content))
        elif media_type == b'application/x-www-form-urlencoded':
            body = parse_qs(await text_reader(content))
            return {name: value[0] for name, value in body.items()}
        elif media_type == b'multipart/form-data':
            if parameters is None:
                raise ValueError(
                    'Missing content type parameters for multipart/form-data'
                )
            return {
                name: value[0]
                for name, value in parse_multipart(
                    io.StringIO(await text_reader(content)),
                    {key.decode('utf-8'): val for key,
                     val in parameters.items()}
                ).items()
            }
        else:
            raise RuntimeError(
                f"Unsupported content type: {media_type.decode('ascii')}"
            )

    async def _handle_query_or_mutation(
            self,
            scope: Scope,
            info: Info,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> HttpResponse:
        LOGGER.debug("Processing a query or mutation.")

        result = await self.query(
            query,
            variables,
            operation_name,
            scope,
            info
        )

        response: Dict[str, Any] = {'data': result.data}
        if result.errors:
            response['errors'] = [
                error.formatted for error in result.errors]

        text = self.dumps(response)
        headers = [
            (b'content-type', b'application/json'),
            (b'content-length', str(len(text)).encode())
        ]

        return 200, headers, text_writer(text)

    def _handle_subscription_redirect(
            self,
            scope: Scope,
            body: Mapping[str, Any]
    ) -> HttpResponse:
        # Handle a subscription by returning 201 (Created) with
        # the url location of the subscription.
        LOGGER.debug("Redirecting subscription request.")
        scheme = scope['scheme']
        host = cast(
            bytes,
            header.find(  # type: ignore
                b'host',
                scope['headers'],
                b'localhost'
            )
        ).decode()
        path = self.path_prefix + '/subscriptions'
        query_string = urlencode(
            {
                name.encode('utf-8'): self.dumps(value).encode('utf-8')
                for name, value in body.items()
            }
        )
        location = f'{scheme}://{host}{path}?{query_string}'.encode('ascii')
        headers = [
            (b'access-control-expose-headers', b'location'),
            (b'location', location)
        ]
        return response_code.CREATED, headers

    async def _handle_streaming_subscription(
            self,
            scope: Scope,
            info: Info,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> HttpResponse:

        # If unspecified default to server sent events as they have better support.
        accept = cast(
            bytes,
            header.find(b'accept', scope['headers'], b'text/event-stream')
        )
        content_type = (
            b'application/stream+json'
            if accept == b'application/json'
            else accept
        )

        result = await self.subscribe(
            query,
            variables,
            operation_name,
            scope,
            info
        )

        is_sse = content_type == b'text/event-stream'
        encode = partial(_encode_sse if is_sse else _encode_json, self.dumps)
        nudge = b':\n\n' if is_sse else b'\n'

        # Make an async iterator for the subscription results.
        async def send_events(zero_event: ZeroEvent) -> AsyncIterable[bytes]:
            LOGGER.debug('Streaming subscription started.')

            try:
                zero_event.increment()

                async for val in cancellable_aiter(
                        result,
                        self.cancellation_event,
                        timeout=self.ping_interval
                ):
                    yield encode(val)
                    yield nudge  # Give the ASGI server a nudge.

            except asyncio.CancelledError:
                LOGGER.debug("Streaming subscription cancelled.")
            except Exception as error:  # pylint: disable=broad-except
                LOGGER.exception("Streaming subscription failed.")
                # If the error is not caught the client fetch will fail, however
                # the status code and headers have already been sent. So rather
                # than let the fetch fail we send a GraphQL response with no
                # data and the error and close gracefully.
                if not isinstance(error, GraphQLError):
                    error = GraphQLError(
                        'Execution error',
                        original_error=error
                    )
                val = ExecutionResult(None, [error])
                yield encode(val)
                yield nudge  # Give the ASGI server a nudge.
            finally:
                zero_event.decrement()

            LOGGER.debug("Streaming subscription stopped.")

        headers = [
            (b'cache-control', b'no-cache'),
            (b'content-type', content_type),
            (b'connection', b'keep-alive')
        ]

        return response_code.OK, headers, send_events(self.subscription_count)

    @abstractmethod
    async def subscribe(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
            scope: Scope,
            info: Info
    ) -> MapAsyncIterator:
        """Execute a subscription.

        Args:
            query (str): The subscription query.
            variables (Optional[Dict[str, Any]]): Optional variables.
            operation_name (Optional[str]): An optional operation name.
            scope (Scope): The ASGI scope.
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
            scope: Scope,
            info: Info
    ) -> ExecutionResult:
        """Execute a query

        Args:
            query (str): The subscription query.
            variables (Optional[Dict[str, Any]]): Optional variables.
            operation_name (Optional[str]): An optional operation name.
            scope (Scope): The ASGI scope.
            info (Info): The application info.

        Returns:
            ExecutionResult: The query results.
        """
