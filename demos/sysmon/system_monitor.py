"""
System Monitor
"""

import asyncio
import logging

from asyncio import Lock, Queue
from datetime import datetime
from math import nan

import psutil

from graphql.pyutils import snake_to_camel as camelcase
from typing import List, Mapping, Any

logger = logging.getLogger(__name__)


class SystemMonitor:
    """System Monitor"""

    def __init__(self, poll_interval_seconds: float = 30) -> None:
        self.cancellation_token = asyncio.Event()
        self.poll_interval_seconds = poll_interval_seconds
        self.cpu_count = psutil.cpu_count(True)
        self.cpu_pct = [nan for _ in range(self.cpu_count)]
        self.listeners: List[Queue] = []
        self.lock = Lock()
        self.latest: dict = {}

    def shutdown(self) -> None:
        """Stop the service"""
        self.cancellation_token.set()

    async def startup(self) -> None:
        """Start the service"""
        self._gather_data()
        while not self.cancellation_token.is_set():
            try:
                await asyncio.wait_for(
                    self.cancellation_token.wait(),
                    timeout=self.poll_interval_seconds
                )
            except asyncio.TimeoutError:
                self._gather_data()
                await self.notify_listeners()

    def _gather_data(self) -> None:
        logger.debug('Getting statistics')
        cpu_times = psutil.cpu_times(True)
        cpu_stats = psutil.cpu_stats()
        cpu_pct = psutil.cpu_percent(None, True)
        self.latest = {
            'timestamp': datetime.utcnow(),
            'cpu': {
                'count': self.cpu_count,
                'percent': psutil.cpu_percent(None, False),
                'cores': [
                    {
                        'percent': cpu_pct[i],
                        'times': {
                            camelcase(k): getattr(cpu_times[i], k)
                            for k in cpu_times[i]._fields
                        }

                    }
                    for i in range(self.cpu_count)
                ],
                'stats': {camelcase(k): getattr(cpu_stats, k) for k in cpu_stats._fields}
            }
        }

    async def notify_listeners(self) -> None:
        """Notify the listeners of new data"""
        await self.lock.acquire()
        try:
            for listener in self.listeners:
                await self.notify_listener(listener, self.latest)
        finally:
            self.lock.release()

    @classmethod
    async def notify_listener(cls, listener: Queue, message: Mapping[str, Any]) -> None:
        """Notify a listener"""
        await listener.put(message)

    async def listen(self) -> Queue:
        """Add a listener"""
        listener: "Queue[dict]" = asyncio.Queue()

        await self.lock.acquire()
        try:
            await self.notify_listener(listener, self.latest)
            self.listeners.append(listener)
            return listener
        finally:
            self.lock.release()

    async def unlisten(self, listener: Queue) -> None:
        """Remove the listener"""
        await self.lock.acquire()
        try:
            self.listeners.remove(listener)
        finally:
            self.lock.release()
