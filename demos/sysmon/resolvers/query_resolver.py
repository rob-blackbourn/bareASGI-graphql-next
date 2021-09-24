"""
Query Resolvers
"""

import logging

from bareasgi import HttpRequest
from graphql import GraphQLResolveInfo

from ..system_monitor import SystemMonitor

logger = logging.getLogger(__name__)

# pylint: disable=unused-argument


async def get_latest(root, info: GraphQLResolveInfo, *args, **kwargs):
    """Get the latest stats"""
    request: HttpRequest = info.context
    system_monitor: SystemMonitor = request.info['system_monitor']
    data = system_monitor.latest
    print(data)
    return data
