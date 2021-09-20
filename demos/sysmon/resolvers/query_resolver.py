"""
Query Resolvers
"""

import logging

from graphql import GraphQLResolveInfo

from ..system_monitor import SystemMonitor

logger = logging.getLogger(__name__)

# pylint: disable=unused-argument


async def get_latest(root, info: GraphQLResolveInfo, *args, **kwargs):
    """Get the latest stats"""
    system_monitor: SystemMonitor = info.context['info']['system_monitor']
    data = system_monitor.latest
    print(data)
    return data
