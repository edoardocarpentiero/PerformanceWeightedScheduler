"""
Modulo 1 - Performance Collector
Servizio logico integrato in cinder-volume.
Coordina raccolta metriche e pubblicazione verso lo scheduler.
"""

from __future__ import annotations
from typing import Any, Dict, List

from performance_metrics import PerformanceMetricsCollector
from scheduler_rpc_api import SchedulerMetricsAPI


class PerformanceCollectorService:
    def __init__(self) -> None:
        self.collector = PerformanceMetricsCollector()
        self.rpc_api = SchedulerMetricsAPI()

    def publish_all_backend_metrics(self, context: Any, backends: List[Dict[str, str]]) -> None:
        """Raccoglie e pubblica le metriche di tutti i backend.

        Ogni elemento della lista `backends` deve contenere:
        - backend
        - storage_type
        - test_path
        """
        for backend in backends:
            metrics = self.collector.collect_fio_metrics(
                backend_name=backend["backend"],
                storage_type=backend["storage_type"],
                test_path=backend["test_path"],
            )
            self.rpc_api.push_backend_metrics(context, metrics)

    def get_backend_metrics(self, backend_name: str, storage_type: str, test_path: str) -> Dict[str, Any]:
        """Usato nel fallback on-demand lato scheduler."""
        return self.collector.collect_fio_metrics(
            backend_name=backend_name,
            storage_type=storage_type,
            test_path=test_path,
        )
