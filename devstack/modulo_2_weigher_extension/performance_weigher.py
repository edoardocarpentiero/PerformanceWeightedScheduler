from __future__ import annotations

from typing import Any, Dict

from oslo_log import log as logging

from cinder.scheduler import weights
from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    BackendMetricsCache,
)

LOG = logging.getLogger(__name__)


class PerformanceWeigher(weights.BaseHostWeigher):
    CACHE: BackendMetricsCache | None = None

    @classmethod
    def set_cache(cls, cache: BackendMetricsCache) -> None:
        cls.CACHE = cache

    def weight_multiplier(self) -> float:
        return 1.0

    def _weigh_object(self, host_state: Any, weight_properties: Dict[str, Any]) -> float:
        backend_name = self._extract_backend_name(host_state)

        metrics = self.CACHE.get(backend_name) if self.CACHE else None
        if metrics is None or (self.CACHE and self.CACHE.is_stale(backend_name)):
            LOG.info(
                "Metrics cache miss/stale for backend '%s', using penalized score",
                backend_name,
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

        LOG.info(
            "Backend '%s': free=%s iops=%s latency=%s throughput=%s saturation=%s score=%s",
            backend_name,
            free_capacity,
            iops,
            latency_ms,
            throughput_kb_s,
            saturation_pct,
            score,
        )

        return score

    @staticmethod
    def _extract_backend_name(host_state: Any) -> str:
        host = getattr(host_state, "host", "")
        if "@" in host:
            return host.split("@", 1)[1].split("#", 1)[0]
        return host
