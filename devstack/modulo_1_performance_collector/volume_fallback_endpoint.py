"""
Modulo 1 - Performance Collector
Endpoint RPC esposto da cinder-volume per il fallback on-demand.
"""

from __future__ import annotations
from typing import Any, Dict

from collector_service import PerformanceCollectorService


class VolumeMetricsEndpoint:
    target = None

    def __init__(self) -> None:
        self.collector_service = PerformanceCollectorService()

    def fetch_backend_metrics(
        self,
        context: Any,
        backend_name: str,
        storage_type: str,
        test_path: str,
    ) -> Dict[str, Any]:
        """Restituisce metriche aggiornate per un backend specifico."""
        return self.collector_service.get_backend_metrics(
            backend_name=backend_name,
            storage_type=storage_type,
            test_path=test_path,
        )
