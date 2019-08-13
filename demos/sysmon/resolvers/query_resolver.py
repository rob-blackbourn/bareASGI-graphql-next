"""
Query Resolvers
"""

from graphql import GraphQLResolveInfo
import logging
from ..system_monitor import SystemMonitor

logger = logging.getLogger(__name__)

# pylint: disable=unused-argument
async def get_latest(root, info: GraphQLResolveInfo, *args, **kwargs):
    """Get the latest stats"""
    system_monitor: SystemMonitor = info.context['system_monitor']
    data = system_monitor.latest
    return data
