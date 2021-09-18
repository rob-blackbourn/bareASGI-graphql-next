"""
Server
"""

import asyncio
import logging
import os
from typing import Optional

from hypercorn.asyncio import serve
from hypercorn.config import Config
import uvicorn

from sysmon.app import make_application

LOGGER = logging.getLogger(__name__)


def initialise_logging() -> None:
    """Initialise logging"""
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'simple': {
                'format': "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        'handlers': {
            'stdout': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            __name__: {
                'level': 'DEBUG',
                'handlers': ['stdout'],
                'propagate': False
            },
            'bareasgi_graphql_next': {
                'level': 'DEBUG',
                'handlers': ['stdout'],
                'propagate': False
            },
            'bareasgi': {
                'level': 'DEBUG',
                'handlers': ['stdout'],
                'propagate': False
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['stdout']
        }
    })


def start_uvicorn_server(
        host: str,
        port: int,
        ssl_enabled: bool = False,
        keyfile: Optional[str] = None,
        certfile: Optional[str] = None
) -> None:
    """Start the uvicorn server"""
    app = make_application()

    kwargs = {
        'host': host,
        'port': port,
        # 'loop': 'asyncio'
    }

    if ssl_enabled:
        kwargs['ssl_keyfile'] = keyfile
        kwargs['ssl_certfile'] = certfile

    uvicorn.run(app, **kwargs)


def start_hypercorn_server(
        host: str,
        port: int,
        ssl_enabled: bool = False,
        keyfile: Optional[str] = None,
        certfile: Optional[str] = None
) -> None:
    """Start the hypercorn server"""
    app = make_application()

    web_config = Config()
    web_config.bind = [f'{host}:{port}']

    if ssl_enabled:
        web_config.keyfile = keyfile
        web_config.certfile = certfile

    asyncio.run(serve(app, web_config))  # type: ignore


def start_http_server(
        http_server: str,
        host: str,
        port: int,
        ssl_enabled: bool = False,
        keyfile: Optional[str] = None,
        certfile: Optional[str] = None
) -> None:
    """Start the http server"""
    if http_server == "uvicorn":
        start_uvicorn_server(host, port, ssl_enabled, keyfile, certfile)
    elif http_server == "hypercorn":
        start_hypercorn_server(host, port, ssl_enabled, keyfile, certfile)
    else:
        LOGGER.error('Unknown http server "%s"', http_server)
        raise Exception(f'Unknown http server "{http_server}"')


def start_server() -> None:
    """Start the server"""

    http_server = 'hypercorn'  # 'hypercorn' or 'uvicorn'
    host = '0.0.0.0'
    port = 9009
    ssl_enabled = True
    certfile = os.path.expanduser('~/.keys/server.crt')
    keyfile = os.path.expanduser('~/.keys/server.key')
    # certfile = os.path.expanduser('~/.keys/www.jetblack.net.crt')
    # keyfile = os.path.expanduser('~/.keys/www.jetblack.net.key')

    initialise_logging()
    start_http_server(http_server, host, port, ssl_enabled, keyfile, certfile)
    logging.shutdown()


if __name__ == "__main__":
    start_server()
