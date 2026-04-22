from __future__ import annotations

from typing import Any, Dict

from cinder.scheduler import weights
from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    BackendMetricsCache,
)


class PerformanceWeigher(weights.BaseHostWeigher):
    def __init__(
        self,
        cache: BackendMetricsCache,
    ) -> None:
        super().__init__()
        self.cache = cache

        print("[DEBUG][weigher] PerformanceWeigher inizializzato", flush=True)

    def weight_multiplier(self) -> float:
        return 1.0

    def _weigh_object(self, host_state: Any, weight_properties: Dict[str, Any]) -> float:
        backend_name = self._extract_backend_name(host_state)

        print(
            f"[DEBUG][weigher] Calcolo peso per backend '{backend_name}'",
            flush=True,
        )

        metrics = self.cache.get(backend_name)

        if metrics is None or self.cache.is_stale(backend_name):
            print(
                f"[WARN][weigher] Metriche assenti o obsolete per backend '{backend_name}', uso valori penalizzanti",
                flush=True,
            )

            metrics = {
                "iops": 0,
                "latency_ms": 9999,
                "throughput_kb_s": 0,
                "saturation_pct": 100,
            }

        free_capacity = float(getattr(host_state, "free_capacity_gb", 0) or 0)
        allocated_capacity = float(getattr(host_state, "allocated_capacity_gb", 0) or 0)

        iops = float(metrics.get("iops", 0))
        latency_ms = float(metrics.get("latency_ms", 9999))
        throughput_kb_s = float(metrics.get("throughput_kb_s", 0))
        saturation_pct = float(metrics.get("saturation_pct", 100))

        score = (
            (free_capacity * 0.4)
            + (iops * 0.01)
            + (throughput_kb_s * 0.001)
            - (latency_ms * 0.5)
            - (saturation_pct * 0.1)
            - (allocated_capacity * 0.1)
        )

        print(
            f"[DEBUG][weigher] Backend '{backend_name}' -> "
            f"free={free_capacity}, alloc={allocated_capacity}, "
            f"iops={iops}, lat={latency_ms}, thr={throughput_kb_s}, "
            f"sat={saturation_pct}, score={score}",
            flush=True,
        )

        return score

    @staticmethod
    def _extract_backend_name(host_state: Any) -> str:
        host = getattr(host_state, "host", "")
        if "@" in host:
            return host.split("@", 1)[1].split("#", 1)[0]
        return host