"""GraphQL Base WebSocket instance"""

from abc import ABCMeta, abstractmethod
import asyncio
import json
import logging
from typing import (
    Any,
    Dict,
    Mapping,
    MutableMapping,
    Optional,
    AsyncIterator,
    Tuple,
    Union,
    List,
    Set
)

from baretypes import Info, Scope, WebSocket
import graphql
from graphql import ExecutionResult, GraphQLError
from graphql.subscription.map_async_iterator import MapAsyncIterator

from .utils import has_subscription

logger = logging.getLogger(__name__)

WS_INTERNAL_ERROR = 1011
WS_PROTOCOL = "graphql-ws"

GQL_CONNECTION_INIT = "connection_init"  # Client -> Server
GQL_CONNECTION_ACK = "connection_ack"  # Server -> Client
GQL_CONNECTION_ERROR = "connection_error"  # Server -> Client
GQL_CONNECTION_KEEP_ALIVE = "ka"  # Server -> Client
GQL_CONNECTION_TERMINATE = "connection_terminate"  # Client -> Server
GQL_START = "start"  # Client -> Server
GQL_DATA = "data"  # Server -> Client
GQL_ERROR = "error"  # Server -> Client
GQL_COMPLETE = "complete"  # Server -> Client
GQL_STOP = "stop"  # Client -> Server


class ProtocolError(Exception):
    """A protocol error"""


Id = Union[str, int]


class GraphQLWebSocketHandlerInstanceBase(metaclass=ABCMeta):
    """A GraphQL WebSocket handler instance"""

    def __init__(self, web_socket: WebSocket, scope: Scope, info: Info) -> None:
        self.web_socket = web_socket
        self.scope = scope
        self.info = info
        self._subscriptions: MutableMapping[Id, asyncio.Future] = {}
        self._is_closed = False

    async def start(self, subprotocols: List[str]):
        """Start the WebSocket connection

        Args:
            subprotocols (List[str]): Optional sub protocols

        Raises:
            ProtocolError: If the protocol is not supported
        """
        if WS_PROTOCOL not in subprotocols:
            raise ProtocolError(f"Expected subprotocol '{WS_PROTOCOL}")
        await self.web_socket.accept(WS_PROTOCOL)

        _type = GQL_CONNECTION_KEEP_ALIVE

        read_task: Optional[asyncio.Task] = None
        pending: Set[asyncio.Future] = set()

        while not (self._is_closed or _type in (GQL_CONNECTION_ERROR, GQL_CONNECTION_TERMINATE)):

            # We need to wait for the websocket and the subscriptions.
            if read_task is None or read_task not in pending:
                read_task = asyncio.create_task(self._read_message())
                pending.add(read_task)
            for task in self._subscriptions.values():
                if task not in pending:
                    pending.add(task)

            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                if task == read_task:
                    try:
                        type_, id_, payload = task.result()
                        await self._on_message(type_, id_, payload)
                        read_task = None
                    except EOFError:
                        self._is_closed = True
                        for pending_task in pending:
                            await self._stop_subscription(pending_task)
                            self._remove_subscription(pending_task)
                else:
                    # Subscription tasks are done when they complete or are cancelled.
                    self._remove_subscription(task)

        await self._unsubscribe_all()
        if not self._is_closed:
            await self.web_socket.close()

    async def _read_message(self) -> Tuple[str, Optional[Id], Optional[dict]]:
        text = await self.web_socket.receive()
        if text is None:
            raise EOFError

        if not isinstance(text, str):
            raise ProtocolError('Expected the message to be a string.')

        message: Mapping[str, Any] = json.loads(text)
        if not isinstance(message, dict):
            raise ProtocolError('Expected the message to be an object.')

        type_: Optional[str] = message['type']
        if not isinstance(type_, str):
            raise ProtocolError("Expected field 'type' to be a string")

        id_: Optional[Id] = message.get('id')
        if not (id_ is None or isinstance(id_, str) or isinstance(id_, int)):
            raise ProtocolError("Expected field 'id' to be an string?")

        payload = message.get('payload')
        if not (payload is None or isinstance(payload, dict)):
            raise ProtocolError("Expected field 'payload' to be an object?")

        return type_, id_, payload

    async def _on_message(self, type_: str, id_: Optional[Id], payload: Optional[dict]):

        if type_ == GQL_CONNECTION_INIT:
            await self._on_connection_init(id_, payload)
        elif type_ == GQL_CONNECTION_TERMINATE:
            await self._on_connection_terminate()
        elif type_ == GQL_START:
            await self._on_start(id_, payload)
        elif type_ == GQL_STOP:
            if id_ is None:
                raise ProtocolError("Can't stop a subscription with no index")
            await self._on_stop(id_)
        elif type_ == GQL_CONNECTION_KEEP_ALIVE:
            pass
        else:
            raise ProtocolError(f"Received unknown message type '{type_}'.")

    # pylint: disable=unused-argument
    async def _on_connection_init(self, id_: Optional[Id], connection_params: Optional[Any]):
        try:
            await self.web_socket.send(self._to_message('connection_ack', id_))
        except Exception as error:
            await self._send_error(GQL_CONNECTION_ERROR, id_, error)
            await self.web_socket.close(WS_INTERNAL_ERROR)
            raise

    async def _on_connection_terminate(self):
        await self.web_socket.close(WS_INTERNAL_ERROR)

    @abstractmethod
    async def subscribe(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> MapAsyncIterator:
        """Execute a subscription.

        Args:
            query (str): The subscription query.
            variables (Optional[Dict[str, Any]]): Optional variables.
            operation_name (Optional[str]): An optional operation name.

        Returns:
            MapAsyncIterator: An asynchronous iterator of the results.
        """

    @abstractmethod
    async def query(
            self,
            query: str,
            variables: Optional[Dict[str, Any]],
            operation_name: Optional[str]
    ) -> ExecutionResult:
        """Execute a query

        Args:
            query (str): The subscription query.
            variables (Optional[Dict[str, Any]]): Optional variables.
            operation_name (Optional[str]): An optional operation name.

        Returns:
            ExecutionResult: The query results.
        """

    async def _on_start(self, id_: Optional[Id], payload: Optional[Union[list, dict]]):
        try:
            # An id is required for a start operation.
            if id_ is None:
                raise ProtocolError("required 'id' field must be an int.")

            if id_ in self._subscriptions:
                await self._unsubscribe(id_)
                del self._subscriptions[id_]

            query, variable_values, operation_name = self._parse_start_payload(
                payload)

            document = graphql.parse(query)
            # noinspection PyUnresolvedReferences
            if has_subscription(document):
                result: Union[MapAsyncIterator, ExecutionResult] = await self.subscribe(
                    query,
                    variable_values,
                    operation_name
                )
            else:
                result = await self.query(
                    query,
                    variable_values,
                    operation_name
                )

            if isinstance(result, ExecutionResult):
                await self._send_execution_result(id_, result)
                return True

            self._add_subscription(id_, result)

        except Exception as error:  # pylint: disable=broad-except
            await self._send_error(GQL_ERROR, id_, error)

    def _add_subscription(self, id_: Id, result: AsyncIterator) -> None:
        self._subscriptions[id_] = asyncio.create_task(
            self._process_subscription(id_, result)
        )

    def _remove_subscription(self, future: asyncio.Future) -> None:
        id_ = next(k for k, v in self._subscriptions.items() if v == future)
        del self._subscriptions[id_]

    async def _process_subscription(self, id_: Id, result: AsyncIterator) -> AsyncIterator:
        try:
            async for val in result:
                await self._send_execution_result(id_, val)
            await self.web_socket.send(self._to_message(GQL_COMPLETE, id_))
        except asyncio.CancelledError:
            pass
        except Exception as error:  # pylint: disable=broad-except
            if not isinstance(error, GraphQLError):
                error = GraphQLError('Execution error', original_error=error)
            await self._send_execution_result(
                id_,
                ExecutionResult(errors=[error])
            )
            await self.web_socket.send(self._to_message(GQL_COMPLETE, id_))

        return result

    async def _on_stop(self, id_: Id) -> None:
        await self._unsubscribe(id_)

    @classmethod
    async def _stop_subscription(cls, future: asyncio.Future) -> None:
        future.cancel()
        await future
        result = future.result()
        await result.aclose()

    async def _unsubscribe(self, id_: Id) -> None:
        await self._stop_subscription(self._subscriptions[id_])

    async def _unsubscribe_all(self) -> None:
        # pylint: disable=consider-iterating-dictionary
        for id_ in self._subscriptions.keys():
            await self._unsubscribe(id_)

    async def _send_error(self, type_: str, id_: Optional[Id], error: Exception) -> None:
        await self.web_socket.send(self._to_message(type_, id_, {'message': str(error)}))

    async def _send_execution_result(
            self,
            id_: Id,
            execution_result: ExecutionResult
    ) -> None:
        result: Dict[str, Union[Dict[str, Any], List[Any]]] = dict()

        if execution_result.data:
            result["data"] = execution_result.data

        if execution_result.errors:
            result["errors"] = [
                error.formatted
                for error in execution_result.errors
            ]

        await self.web_socket.send(self._to_message(GQL_DATA, id_, result))

    @classmethod
    def _to_message(
            cls,
            type_: str,
            id_: Optional[Id] = None,
            payload: Optional[Any] = None
    ) -> str:
        message: Dict[str, Any] = {'type': type_}
        if id_ is not None:
            message['id'] = id_
        if payload is not None:
            message['payload'] = payload
        return json.dumps(message)

    @classmethod
    def _parse_start_payload(
            cls,
            payload: Optional[Union[dict, list]]
    ) -> Tuple[str, Optional[Dict[str, Any]], Optional[str]]:

        if not isinstance(payload, dict):
            raise ProtocolError("required 'payload' field must be an object.")

        query = payload.get('query')
        if not isinstance(query, str):
            raise ProtocolError(
                "required 'query' field must be string in 'payload'.")

        variable_values = payload.get('variables')
        if not (variable_values is None or isinstance(variable_values, dict)):
            raise ProtocolError(
                "optional 'variables' field must be object? in 'payload'.")

        operation_name = payload.get('operationName')
        if not (operation_name is None or isinstance(operation_name, str)):
            raise ProtocolError(
                "optional 'operationName' field must be str? in 'payload'.")

        return query, variable_values, operation_name
