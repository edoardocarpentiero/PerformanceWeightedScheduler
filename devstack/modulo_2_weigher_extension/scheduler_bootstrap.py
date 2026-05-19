from __future__ import annotations

import oslo_messaging
from oslo_config import cfg

from cinder.scheduler.performance_weighted_scheduler_module2.scheduler_metrics_endpoint import (
    SchedulerMetricsEndpoint,
)

CONF = cfg.CONF

_CONF_INITIALIZED = False
_PLUGIN_STARTED = False

def _init_conf() -> None:
    global _CONF_INITIALIZED

    if _CONF_INITIALIZED:
        print("[PLUGIN - MD2 >> bootstrap] Configurazione già inizializzata", flush=True)
        return

    CONF(
        args=[],
        project="cinder",
        default_config_files=["/etc/cinder/cinder.conf"],
    )

    _CONF_INITIALIZED = True

    print(
        "[PLUGIN - MD2 >> bootstrap] Configurazione scheduler caricata da /etc/cinder/cinder.conf",
        flush=True,
    )


def initSchedulerPlugin():
    global _PLUGIN_STARTED

    if _PLUGIN_STARTED:
        print("[PLUGIN - MD2 >> bootstrap] Plugin scheduler già inizializzato", flush=True)
        return

    print("[PLUGIN - MD2 >> bootstrap] Avvio inizializzazione plugin scheduler", flush=True)

    _init_conf()

    endpoint = SchedulerMetricsEndpoint()

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

    _PLUGIN_STARTED = True

    print(
        "[PLUGIN - MD2 >> bootstrap] Server RPC scheduler avviato su topic 'scheduler_metrics'",
        flush=True,
    )