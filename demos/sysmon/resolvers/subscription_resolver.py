"""
Subscription resolver
"""

import logging

from bareasgi import HttpRequest
from graphql import GraphQLResolveInfo

from ..system_monitor import SystemMonitor

logger = logging.getLogger(__name__)


async def subscribe_to_systems(_root, info: GraphQLResolveInfo, *_args, **_kwargs):
    """Subscribe to systems"""
    logger.debug('Subscribing to system data')
    request: HttpRequest = info.context
    system_monitor: SystemMonitor = request.info['system_monitor']

    # raise RuntimeError('Oh dear')

    queue = await system_monitor.listen()

    try:
        while True:
            data = await queue.get()
            yield data
    finally:
        logger.debug('Unsubscribing to system data')
        await system_monitor.unlisten(queue)


def resolve_subscriptions(root, _info: GraphQLResolveInfo, *args, **kwargs):
    """Resolve subscriptions"""
    return root
