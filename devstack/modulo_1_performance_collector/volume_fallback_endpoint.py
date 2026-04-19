from __future__ import annotations

from typing import Any, Dict

from oslo_log import log as logging

from cinder.volume.performance_weighted_scheduler_module1.collector_service import (
    PerformanceCollectorService,
)

LOG = logging.getLogger(__name__)


class VolumeMetricsEndpoint:
    target = None

    def __init__(self) -> None:
        LOG.info("Initializing VolumeMetricsEndpoint")
        self.collector_service = PerformanceCollectorService()

    def fetch_backend_metrics(
        self,
        context: Any,
        backend_name: str,
        storage_type: str,
        device_name: str,
    ) -> Dict[str, Any]:
        LOG.info(
            "Received fallback request for backend='%s', storage_type='%s', device_name='%s'",
            backend_name,
            storage_type,
            device_name,
        )

        try:
            metrics = self.collector_service.get_backend_metrics(
                backend_name=backend_name,
                storage_type=storage_type,
                device_name=device_name,
            )

            LOG.info(
                "Fallback metrics collected successfully for backend '%s': %s",
                backend_name,
                metrics,
            )

            return metrics

        except Exception:
            LOG.exception(
                "Failed to fetch fallback metrics for backend '%s'",
                backend_name,
            )
            raise