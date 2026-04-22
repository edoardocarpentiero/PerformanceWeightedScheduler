from __future__ import annotations

from typing import Any, Dict

from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    BackendMetricsCache,
)


class SchedulerMetricsEndpoint:
    def __init__(self, cache: BackendMetricsCache) -> None:
        self.cache = cache
        print("[DEBUG][scheduler_endpoint] Endpoint scheduler inizializzato", flush=True)

    def update_backend_metrics(self, context: Any, metrics: Dict[str, Any]) -> None:
        backend_name = metrics["backend"]

        print(
            f"[DEBUG][scheduler_endpoint] Aggiornamento cache metriche per backend '{backend_name}'",
            flush=True,
        )

        self.cache.put(backend_name, metrics)

        print(
            f"[DEBUG][scheduler_endpoint] Cache aggiornata per backend '{backend_name}'",
            flush=True,
        )