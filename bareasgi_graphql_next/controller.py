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

from bareasgi import (
    Application,
    HttpRequest,
    HttpResponse,
    WebSocketRequest,
    HttpMiddlewareCallback
)
from bareutils import text_reader, text_writer, response_code, header
import graphql
from graphql import (
    ExecutionResult,
    GraphQLError,
    MapAsyncIterator,
    MiddlewareManager
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
    ) -> Application:
        """Add the routes

        Args:
            app (Application): The ASGI application.
            path_prefix (str, optional): The path prefix. Defaults to ''.
            rest_middleware (Optional[HttpMiddlewareCallback], optional): The
                rest middleware. Defaults to None.
            view_middleware (Optional[HttpMiddlewareCallback], optional): The
                view middleware. Defaults to None.

        Returns:
            Application: The application.
        """
        # Add the REST routes.
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

        return app

    async def shutdown(self) -> None:
        """Shutdown the service"""
        self.cancellation_event.set()
        await self.subscription_count.wait()

    async def view_graphiql(self, request: HttpRequest) -> HttpResponse:
        """Render the Graphiql view

        Args:
            request (HttpRequest): The request.

        Returns:
            HttpResponse: The response.
        """

        try:
            host = get_host(request)
            scheme = get_scheme(request)
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
            return HttpResponse(response_code.OK, headers, text_writer(body))

        # pylint: disable=bare-except
        except:
            LOGGER.exception("Failed to handle grahphiql request")

            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return HttpResponse(
                response_code.INTERNAL_SERVER_ERROR,
                headers,
                text_writer(text)
            )

    @abstractmethod
    async def handle_websocket_subscription(self, request: WebSocketRequest) -> None:
        """Handle a websocket subscription

        Args:
            request (WebSocketRequest): The request
        """

    async def handle_graphql(self, request: HttpRequest) -> HttpResponse:
        """A request handler for graphql queries

        Args:
            scope (Scope): The Request

        Returns:
            HttpResponse: The HTTP response to the query request
        """

        try:
            body = await self._get_query_document(request)

            query: str = body['query']
            variables: Optional[Dict[str, Any]] = body.get('variables')
            operation_name: Optional[str] = body.get('operationName')

            query_document = graphql.parse(query)

            if not has_subscription(query_document):
                return await self._handle_query_or_mutation(
                    request,
                    query,
                    variables,
                    operation_name
                )

            # The subscription method is determined by the `allow` header.
            allow = header.find(b'allow', request.scope['headers'], b'GET')
            if allow == b'GET':
                return self._handle_subscription_redirect(request, body)

            return await self._handle_streaming_subscription(
                request,
                query,
                variables,
                operation_name
            )

        # pylint: disable=bare-except
        except:
            LOGGER.exception("Failed to handle graphql query request")

            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return HttpResponse(
                response_code.INTERNAL_SERVER_ERROR,
                headers,
                text_writer(text)
            )

    async def handle_subscription_get(self, request: HttpRequest) -> HttpResponse:
        """Handle a streaming subscription

        Args:
            request (HttpRequest): The request

        Returns:
            HttpResponse: The streaming response
        """

        try:
            LOGGER.debug(
                "Received GET streaming subscription request: http_version='%s'.",
                request.scope['http_version']
            )

            body = {
                name.decode('utf-8'): self.loads(value[0].decode('utf-8'))
                for name, value in cast(
                    Dict[bytes, List[bytes]],
                    parse_qs(request.scope['query_string'])
                ).items()
            }

            query: str = body['query']
            variables: Optional[Dict[str, Any]] = body.get('variables')
            operation_name: Optional[str] = body.get('operationName')

            return await self._handle_streaming_subscription(
                request,
                query,
                variables,
                operation_name
            )

        # pylint: disable=bare-except
        except:
            LOGGER.exception("Failed to handle graphql GET subscription")

            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return HttpResponse(
                response_code.INTERNAL_SERVER_ERROR,
                headers,
                text_writer(text)
            )

    async def handle_subscription_post(self, request: HttpRequest) -> HttpResponse:
        """Handle a streaming subscription

        Args:
            request (HttpRequest): The request

        Returns:
            HttpResponse: A stream response
        """

        try:
            LOGGER.debug(
                "Received POST streaming subscription request: http_version='%s'.",
                request.scope['http_version']
            )

            text = await text_reader(request.body)
            body = self.loads(text)

            query: str = body['query']
            variables: Optional[Dict[str, Any]] = body.get('variables')
            operation_name: Optional[str] = body.get('operationName')

            return await self._handle_streaming_subscription(
                request,
                query,
                variables,
                operation_name
            )

        # pylint: disable=bare-except
        except:
            LOGGER.exception("Failed to handle graphql POST subscription")

            text = 'Internal server error'
            headers = [
                (b'content-type', b'text/plain'),
                (b'content-length', str(len(text)).encode())
            ]
            return HttpResponse(
                response_code.INTERNAL_SERVER_ERROR,
                headers,
                text_writer(text)
            )

    async def _get_query_document(self, request: HttpRequest) -> Mapping[str, Any]:
        content_type = header.content_type(request.scope['headers'])
        if content_type is None:
            raise ValueError('Content type not specified')
        media_type, parameters = content_type

        if media_type == b'application/graphql':
            return {'query': await text_reader(request.body)}
        elif media_type in (b'application/json', b'text/plain'):
            return self.loads(await text_reader(request.body))
        elif media_type == b'application/x-www-form-urlencoded':
            body = parse_qs(await text_reader(request.body))
            return {name: value[0] for name, value in body.items()}
        elif media_type == b'multipart/form-data':
            if parameters is None:
                raise ValueError(
                    'Missing content type parameters for multipart/form-data'
                )
            param_dict = {
                key.decode('utf-8'): val
                for key, val in parameters.items()
            }
            multipart_dict = parse_multipart(
                io.StringIO(await text_reader(request.body)),
                param_dict
            )
            return {
                name: value[0]
                for name, value in multipart_dict.items()
            }
        else:
            raise RuntimeError(
                f"Unsupported content type: {media_type.decode('ascii')}"
            )

    async def _handle_query_or_mutation(
            self,
            request: HttpRequest,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> HttpResponse:
        LOGGER.debug("Processing a query or mutation.")

        result = await self.query(request, query, variables, operation_name)

        response: Dict[str, Any] = {'data': result.data}
        if result.errors:
            response['errors'] = [
                error.formatted for error in result.errors]

        text = self.dumps(response)
        headers = [
            (b'content-type', b'application/json'),
            (b'content-length', str(len(text)).encode())
        ]

        return HttpResponse(response_code.OK, headers, text_writer(text))

    def _handle_subscription_redirect(
            self,
            request: HttpRequest,
            body: Mapping[str, Any]
    ) -> HttpResponse:
        # Handle a subscription by returning 201 (Created) with
        # the url location of the subscription.
        LOGGER.debug("Redirecting subscription request.")
        scheme = request.scope['scheme']
        host = cast(
            bytes,
            header.find(  # type: ignore
                b'host',
                request.scope['headers'],
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
        return HttpResponse(response_code.CREATED, headers)

    async def _handle_streaming_subscription(
            self,
            request: HttpRequest,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> HttpResponse:
        # If unspecified default to server sent events as they have better support.
        accept = cast(
            bytes,
            header.find(
                b'accept', request.scope['headers'], b'text/event-stream')
        )
        content_type = (
            b'application/stream+json'
            if accept == b'application/json'
            else accept
        )

        result = await self.subscribe(request, query, variables, operation_name)

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

        return HttpResponse(
            response_code.OK,
            headers,
            send_events(self.subscription_count)
        )

    @abstractmethod
    async def subscribe(
            self,
            request: HttpRequest,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
    ) -> MapAsyncIterator:
        """Execute a subscription.

        Args:
            request (HttpRequest): The http request.
            query (str): The subscription query.
            variables (Optional[Dict[str, Any]]): Optional variables.
            operation_name (Optional[str]): An optional operation name.

        Returns:
            MapAsyncIterator: An asynchronous iterator of the results.
        """

    @abstractmethod
    async def query(
            self,
            request: HttpRequest,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str],
    ) -> ExecutionResult:
        """Execute a query

        Args:
            request (HttpRequest): The http request.
            query (str): The subscription query.
            variables (Optional[Dict[str, Any]]): Optional variables.
            operation_name (Optional[str]): An optional operation name.

        Returns:
            ExecutionResult: The query results.
        """
