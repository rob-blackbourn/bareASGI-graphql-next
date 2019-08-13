"""
Subscription resolver
"""

from graphql import GraphQLResolveInfo
import logging
from ..system_monitor import SystemMonitor

logger = logging.getLogger(__name__)

# pylint: disable=unused-argument
async def subscribe_to_systems(root, info: GraphQLResolveInfo, *args, **kwargs):
    """Subscribe to systems"""
    logger.debug('Subscribing to system data')
    system_monitor: SystemMonitor = info.context['system_monitor']

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
