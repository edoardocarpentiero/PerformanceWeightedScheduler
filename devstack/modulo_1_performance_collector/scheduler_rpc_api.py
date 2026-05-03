from __future__ import annotations

from typing import Any, Dict

import oslo_messaging
from oslo_config import cfg

CONF = cfg.CONF

_CONF_INITIALIZED = False


def _init_conf() -> None:
    global _CONF_INITIALIZED

    print("[DEBUG][scheduler_rpc_api] ingresso in _init_conf()", flush=True)

    if _CONF_INITIALIZED:
        print("[DEBUG][scheduler_rpc_api] CONF già inizializzato", flush=True)
        return

    CONF(
        args=[],
        project="cinder",
        default_config_files=["/etc/cinder/cinder.conf"],
    )

    _CONF_INITIALIZED = True

    print(
        "[DEBUG][scheduler_rpc_api] Configurazione RPC caricata da "
        "/etc/cinder/cinder.conf",
        flush=True,
    )


class SchedulerMetricsAPI:
    RPC_API_VERSION = "1.0"

    def __init__(self) -> None:
        print("[DEBUG][scheduler_rpc_api] Inizializzazione di SchedulerMetricsAPI", flush=True)

        _init_conf()

        target = oslo_messaging.Target(
            topic="scheduler_metrics",
            version=self.RPC_API_VERSION,
        )

        print(
            f"[DEBUG][scheduler_rpc_api] Target creato: topic='{target.topic}', "
            f"version='{target.version}'",
            flush=True,
        )

        print("[DEBUG][scheduler_rpc_api] Creazione del transport RPC", flush=True)
        transport = oslo_messaging.get_rpc_transport(CONF)

        print("[DEBUG][scheduler_rpc_api] Creazione del client RPC", flush=True)
        self.client = oslo_messaging.get_rpc_client(transport, target)

        print(
            "[DEBUG][scheduler_rpc_api] SchedulerMetricsAPI inizializzato correttamente",
            flush=True,
        )

    def push_backend_metrics(self, context: Any, metrics: Dict[str, Any]) -> None:
        print(
            f"[DEBUG][scheduler_rpc_api] Invio metriche backend per "
            f"backend='{metrics.get('backend')}'",
            flush=True,
        )

        print(
            f"[DEBUG][scheduler_rpc_api] Payload={metrics}",
            flush=True,
        )

        try:
            cctxt = self.client.prepare()
            print("[DEBUG][scheduler_rpc_api] Contesto RPC preparato", flush=True)

            cctxt.cast(context, "update_backend_metrics", metrics=metrics)

            print(
                f"[DEBUG][scheduler_rpc_api] Metriche inviate correttamente per "
                f"backend='{metrics.get('backend')}'",
                flush=True,
            )

        except Exception as exc:
            print(
                f"[ERROR][scheduler_rpc_api] Impossibile inviare le metriche per "
                f"backend='{metrics.get('backend')}': {exc}",
                flush=True,
            )
            raise