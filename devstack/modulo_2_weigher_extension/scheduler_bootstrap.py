from __future__ import annotations

import oslo_messaging
from oslo_config import cfg
from oslo_log import log as logging

from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    BackendMetricsCache,
)
from cinder.scheduler.performance_weighted_scheduler_module2.scheduler_metrics_endpoint import (
    SchedulerMetricsEndpoint,
)
from cinder.scheduler.weights.performance_weigher import PerformanceWeigher

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

_CONF_INITIALIZED = False


def _init_conf() -> None:
    global _CONF_INITIALIZED

    if _CONF_INITIALIZED:
        return

    CONF(
        args=[],
        project="cinder",
        default_config_files=["/etc/cinder/cinder.conf"],
    )

    _CONF_INITIALIZED = True

    LOG.info("Scheduler bootstrap configuration loaded from /etc/cinder/cinder.conf")


def init_scheduler_plugin():
    _init_conf()

    cache = BackendMetricsCache(ttl_seconds=60)
    endpoint = SchedulerMetricsEndpoint(cache=cache)

    transport = oslo_messaging.get_rpc_transport(CONF)
    target = oslo_messaging.Target(
        topic="scheduler_metrics",
        server="scheduler_metrics_server",
    )

    server = oslo_messaging.get_rpc_server(
        transport,
        target,
        [endpoint],
        executor="threading",
    )
    server.start()

    LOG.info("Scheduler metrics RPC server started on topic='scheduler_metrics'")

    weigher = PerformanceWeigher(
        cache=cache,
    )

    return {
        "cache": cache,
        "rpc_server": server,
        "weigher": weigher,
    }