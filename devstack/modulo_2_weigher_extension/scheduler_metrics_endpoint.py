from __future__ import annotations

from typing import Any, Dict

from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    get_metrics_cache,
)


class SchedulerMetricsEndpoint:
    def __init__(self) -> None:
        self.cache = get_metrics_cache()
        print("[PLUGIN - MD2 >> scheduler_endpoint]  Endpoint scheduler inizializzato", flush=True)

    def aggiornaMetricheBackend(self, context: Any, metrics: Dict[str, Any]) -> None:
        backend_name = metrics.get("backend_section")

        print(
            f"[PLUGIN - MD2 >> scheduler_endpoint] Aggiornamento cache metriche per backend '{backend_name}'",
            flush=True,
        )

        self.cache.put(backend_name, metrics)

        print(
            f"[PLUGIN - MD2 >> scheduler_endpoint] Cache aggiornata per backend '{backend_name}'",
            flush=True,
        )