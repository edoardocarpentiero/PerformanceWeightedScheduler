"""
Modulo 1 - Performance Collector
Client RPC per inviare metriche a cinder-scheduler.
"""

from __future__ import annotations
from typing import Any, Dict
import oslo_messaging
from oslo_config import cfg

CONF = cfg.CONF


class SchedulerMetricsAPI:
    RPC_API_VERSION = "1.0"

    def __init__(self) -> None:
        target = oslo_messaging.Target(
            topic="scheduler_metrics",
            version=self.RPC_API_VERSION,
        )
        transport = oslo_messaging.get_rpc_transport(CONF)
        self.client = oslo_messaging.get_rpc_client(transport, target)

    def push_backend_metrics(self, context: Any, metrics: Dict[str, Any]) -> None:
        """Invio asincrono delle metriche verso lo scheduler."""
        cctxt = self.client.prepare()
        cctxt.cast(context, "update_backend_metrics", metrics=metrics)
