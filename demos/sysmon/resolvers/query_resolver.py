from graphql import GraphQLResolveInfo
import logging
from ..system_monitor import SystemMonitor

logger = logging.getLogger(__name__)


async def get_latest(root, info: GraphQLResolveInfo, *args, **kwargs):
    system_monitor: SystemMonitor = info.context['system_monitor']
    data = system_monitor.latest
    return data
