from __future__ import annotations

from typing import Any, Dict

from cinder.scheduler import weights
from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    get_metrics_cache,
)


class PerformanceWeigher(weights.BaseHostWeigher):
    def __init__(self) -> None:
        super().__init__()

        self.cache = get_metrics_cache()

        print("[DEBUG][weigher] PerformanceWeigher inizializzato", flush=True)

    def weight_multiplier(self) -> float:
        return 1.0

    def _weigh_object(self, host_state: Any, weight_properties: Dict[str, Any]) -> float:
        host_state_name = getattr(host_state, "host", "")

        print(
            f"[DEBUG][weigher] Calcolo peso per host_state '{host_state_name}'",
            flush=True,
        )

        metrics = self.cache.find_by_host_state(host_state_name)

        if metrics is None:
            print(
                f"[WARN][weigher] Metriche non disponibili per host_state "
                f"'{host_state_name}', uso valori penalizzanti",
                flush=True,
            )

            metrics = {
                "iops": 0,
                "latency_ms": 9999,
                "throughput_kb_s": 0,
                "saturation_pct": 100,
                "storage_type_plugin": "unknown",
            }

        # === Metriche ===
        iops = float(metrics.get("iops", 0))
        latency_ms = float(metrics.get("latency_ms", 9999))
        throughput_kb_s = float(metrics.get("throughput_kb_s", 0))
        saturation_pct = float(metrics.get("saturation_pct", 100))
        storage_type_plugin = str(metrics.get("storage_type_plugin", "unknown")).upper()

        # === Bonus storage ===
        if storage_type_plugin == "SSD":
            storage_bonus = 20.0
        else:
            storage_bonus = 0.0

        # === Calcolo score ===
        score = (
            + (iops * 0.01)
            + (throughput_kb_s * 0.001)
            - (latency_ms * 0.5)
            - (saturation_pct * 0.1)
            + storage_bonus
        )

        print(
            f"[DEBUG][weigher] HostState '{host_state_name}' -> "
            f"iops={iops}, latency={latency_ms}, throughput={throughput_kb_s}, "
            f"saturation={saturation_pct}, storage={storage_type_plugin}, "
            f"bonus={storage_bonus}, score={score}",
            flush=True,
        )

        return score