from __future__ import annotations

from typing import Any, Dict

from oslo_log import log as logging

from collector_service import PerformanceCollectorService

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
        test_path: str,
    ) -> Dict[str, Any]:
        LOG.info(
            "Received fallback request for backend='%s', storage_type='%s', test_path='%s'",
            backend_name,
            storage_type,
            test_path,
        )

        try:
            metrics = self.collector_service.get_backend_metrics(
                backend_name=backend_name,
                storage_type=storage_type,
                test_path=test_path,
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