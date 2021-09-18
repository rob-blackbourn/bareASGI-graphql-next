"""
Subscription resolver
"""

import logging

from graphql import GraphQLResolveInfo, GraphQLError

from ..system_monitor import SystemMonitor

logger = logging.getLogger(__name__)


async def subscribe_to_systems(_root, info: GraphQLResolveInfo, *_args, **_kwargs):
    """Subscribe to systems"""
    logger.debug('Subscribing to system data')
    system_monitor: SystemMonitor = info.context['info']['system_monitor']

    # raise RuntimeError('Oh dear')

    queue = await system_monitor.listen()

    try:
        while True:
            data = await queue.get()
            yield data
    finally:
        logger.debug('Unsubscribing to system data')
        await system_monitor.unlisten(queue)


def resolve_subscriptions(root, info: GraphQLResolveInfo, *args, **kwargs):
    """Resolve subscriptions"""
    return root
