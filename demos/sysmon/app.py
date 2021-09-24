"""
The ASGI Application
"""

import asyncio
import logging
import string

from bareasgi import Application, HttpRequest, HttpResponse, LifespanRequest
from bareasgi_cors import CORSMiddleware
from bareutils import text_writer, header
import pkg_resources

from bareasgi_graphql_next import add_graphql_next

from .system_monitor import SystemMonitor
from .schema import schema

logger = logging.getLogger(__name__)


async def start_service(request: LifespanRequest) -> None:
    """Start the service"""
    system_monitor = SystemMonitor(1)

    request.info['system_monitor'] = system_monitor
    request.info['system_monitor_task'] = asyncio.create_task(
        system_monitor.startup())


async def stop_service(request: LifespanRequest) -> None:
    """Stop the service"""
    system_monitor: SystemMonitor = request.info['system_monitor']
    system_monitor_task: asyncio.Task = request.info['system_monitor_task']
    system_monitor.shutdown()
    await system_monitor_task


# pylint: disable=unused-argument
async def graphql_handler(request: HttpRequest) -> HttpResponse:
    """Handle a graphql request"""
    host = header.find(b'host', request.scope['headers']).decode()
    sse_url = f"{request.scope['scheme']}://{host}/sysmon/graphql"
    html = request.info['page_template'].substitute(sse_url=sse_url)
    return HttpResponse(200, [(b'content-type', b'text/html')], text_writer(html))


def make_application() -> Application:
    """Make the application"""

    page_filename = pkg_resources.resource_filename(__name__, "page.html")
    with open(page_filename, 'rt') as file_ptr:
        page = file_ptr.read()

    cors_middleware = CORSMiddleware()
    info: dict = {'page_template': string.Template(page)}
    app = Application(
        info=info,
        startup_handlers=[start_service],
        shutdown_handlers=[stop_service],
        middlewares=[cors_middleware]
    )
    add_graphql_next(app, schema, '/sysmon')

    app.http_router.add({'GET'}, '/sysmon/graphql2', graphql_handler)

    return app
