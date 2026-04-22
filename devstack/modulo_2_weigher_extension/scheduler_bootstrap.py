from __future__ import annotations

import oslo_messaging
from oslo_config import cfg

from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    BackendMetricsCache,
)
from cinder.scheduler.performance_weighted_scheduler_module2.scheduler_metrics_endpoint import (
    SchedulerMetricsEndpoint,
)
from cinder.scheduler.weights.performance_weigher import PerformanceWeigher

CONF = cfg.CONF

_CONF_INITIALIZED = False


def _init_conf() -> None:
    global _CONF_INITIALIZED

    if _CONF_INITIALIZED:
        print("[DEBUG][bootstrap] Configurazione già inizializzata", flush=True)
        return

    CONF(
        args=[],
        project="cinder",
        default_config_files=["/etc/cinder/cinder.conf"],
    )

    _CONF_INITIALIZED = True

    print(
        "[DEBUG][bootstrap] Configurazione scheduler caricata da /etc/cinder/cinder.conf",
        flush=True,
    )


def init_scheduler_plugin():
    print("[DEBUG][bootstrap] Avvio inizializzazione plugin scheduler", flush=True)

    _init_conf()

    cache = BackendMetricsCache(ttl_seconds=60)

    endpoint = SchedulerMetricsEndpoint(cache=cache)

    print("[DEBUG][bootstrap] Creazione transport RPC", flush=True)

    transport = oslo_messaging.get_rpc_transport(CONF)

    target = oslo_messaging.Target(
        topic="scheduler_metrics",
        server="scheduler_metrics_server",
    )

    print("[DEBUG][bootstrap] Creazione server RPC", flush=True)

    server = oslo_messaging.get_rpc_server(
        transport,
        target,
        [endpoint],
        executor="threading",
    )

    server.start()

    print(
        "[DEBUG][bootstrap] Server RPC scheduler avviato su topic 'scheduler_metrics'",
        flush=True,
    )

    weigher = PerformanceWeigher(
        cache=cache,
    )

    print("[DEBUG][bootstrap] PerformanceWeigher inizializzato", flush=True)

    return {
        "cache": cache,
        "rpc_server": server,
        "weigher": weigher,
    }