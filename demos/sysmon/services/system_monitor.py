import asyncio
from asyncio import Lock, Queue
from datetime import datetime
from math import nan
import psutil
from stringcase import camelcase
from typing import List, Mapping, Any


class SystemMonitor:

    def __init__(self, poll_interval_seconds: float = 30) -> None:
        self.cancellation_token = asyncio.Event()
        self.poll_interval_seconds = poll_interval_seconds
        self.cpu_count = psutil.cpu_count(True)
        self.cpu_pct = [nan for _ in range(self.cpu_count)]
        self.listeners: List[Queue] = []
        self.lock = Lock()

    async def shutdown(self) -> None:
        self.cancellation_token.set()

    async def startup(self) -> None:
        self.cpu_pct = psutil.cpu_percent(None, True)
        while not self.cancellation_token.is_set():
            try:
                await asyncio.wait_for(self.cancellation_token.wait(), timeout=self.poll_interval_seconds)
            except asyncio.TimeoutError:
                self.cpu_pct = psutil.cpu_percent(None, True)
                await self.notify_listeners()

    @property
    async def latest(self) -> Mapping[str, Any]:
        cpu_times = psutil.cpu_times(True)
        cpu_stats = psutil.cpu_stats()
        return {
            'time': datetime.utcnow(),
            'count': self.cpu_count,
            'cpu': [
                {
                    'percent': self.cpu_pct[i],
                    'times': {camelcase(k): getattr(cpu_times[i], k) for k in cpu_times[i].fields},
                    'stats': {camelcase(k): getattr(cpu_stats[i], k) for k in cpu_stats[i].fields}
                }
                for i in range(self.cpu_count)
            ]
        }

    async def notify_listeners(self) -> None:
        await self.lock.acquire()
        try:
            message = await self.latest
            for listener in self.listeners:
                await self.notify_listener(listener, message)
        finally:
            self.lock.release()

    @classmethod
    async def notify_listener(cls, listener: Queue, message: Mapping[str, Any]) -> None:
        await listener.put(message)

    async def listen(self) -> Queue:
        listener = asyncio.Queue()

        await self.lock.acquire()
        try:
            await self.notify_listener(listener, await self.latest)
            self.listeners.append(listener)
            return listener
        finally:
            self.lock.release()

    async def unlisten(self, listener: Queue) -> None:
        await self.lock.acquire()
        try:
            self.listeners.remove(listener)
        finally:
            self.lock.release()
