from __future__ import annotations

from typing import Any, Dict

from oslo_log import log as logging

from cinder.scheduler.performance_weighted_scheduler_module2.metrics_cache import (
    BackendMetricsCache,
)

LOG = logging.getLogger(__name__)


class SchedulerMetricsEndpoint:
    def __init__(self, cache: BackendMetricsCache) -> None:
        self.cache = cache

    def update_backend_metrics(self, context: Any, metrics: Dict[str, Any]) -> None:
        backend_name = metrics["backend"]
        LOG.info("Updating metrics cache for backend '%s'", backend_name)
        self.cache.put(backend_name, metrics)
