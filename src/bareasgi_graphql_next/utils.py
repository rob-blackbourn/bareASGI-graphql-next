import asyncio
from asyncio import Event
from typing import Tuple, Mapping, MutableMapping, Iterator, AsyncIterator


def _parseparam(s: bytes) -> Iterator[bytes]:
    while s[:1] == b';':
        s = s[1:]
        end = s.find(b';')
        while end > 0 and (s.count(b'"', 0, end) - s.count(b'\\"', 0, end)) % 2:
            end = s.find(b';', end + 1)
        if end < 0:
            end = len(s)
        f = s[:end]
        yield f.strip()
        s = s[end:]


def parse_header(line: bytes) -> Tuple[bytes, Mapping[bytes, bytes]]:
    """Parse a Content-type like header.

    Return the main content-type and a dictionary of options.

    """
    parts = _parseparam(b';' + line)
    key = parts.__next__()
    params: MutableMapping[bytes, bytes] = {}
    for p in parts:
        i = p.find(b'=')
        if i >= 0:
            name = p[:i].strip().lower()
            value = p[i + 1:].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace(b'\\\\', b'\\').replace(b'\\"', b'"')
            params[name] = value
    return key, params


async def cancellable_aiter(
        async_iterator: AsyncIterator,
        cancellation_event: Event,
        *,
        cancel_pending: bool = True
) -> AsyncIterator:
    """Create a cancellable async iterator.

    :param async_iterator: The async iterator to wrap
    :param cancellation_event: The asyncio Event to controll cancellation.
    :param cancel_pending: If True cancel pending tasks, otherwaise wait them.
    :return: The wrapped async iterator
    """
    cancellation_task = asyncio.create_task(cancellation_event.wait())
    result_iter = async_iterator.__aiter__()
    while not cancellation_event.is_set():
        done, pending = await asyncio.wait(
            [cancellation_task, result_iter.__anext__()],
            return_when=asyncio.FIRST_COMPLETED
        )
        for done_task in done:
            if done_task == cancellation_task:
                for pending_task in pending:
                    if cancel_pending:
                        pending_task.cancel()
                    else:
                        await pending_task
                        yield pending_task.result()
                break
            else:
                yield done_task.result()
