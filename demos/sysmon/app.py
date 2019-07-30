import asyncio
import logging
from bareasgi import Application
from bareasgi_cors import CORSMiddleware
from bareasgi_graphql_next import add_graphql_next
from baretypes import Scope, Info
from .system_monitor import SystemMonitor
from .schema import schema

logger = logging.getLogger(__name__)


async def start_service(scope: Scope, info: Info, request) -> None:
    system_monitor = SystemMonitor(5)

    info['system_monitor'] = system_monitor
    info['system_monitor_task'] = asyncio.create_task(system_monitor.startup())


async def stop_service(scope: Scope, info: Info, request) -> None:
    system_monitor: SystemMonitor = info['system_monitor']
    system_monitor_task: asyncio.Task = info['system_monitor_task']
    system_monitor.shutdown()
    await system_monitor_task


def make_application() -> Application:
    cors_middleware = CORSMiddleware()
    app = Application(
        info=dict(),
        startup_handlers=[start_service],
        shutdown_handlers=[stop_service],
        middlewares=[cors_middleware]
    )
    add_graphql_next(app, schema, path_prefix='/test')
    return app
