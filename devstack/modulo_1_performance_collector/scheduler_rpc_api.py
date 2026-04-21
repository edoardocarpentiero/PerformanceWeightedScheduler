from __future__ import annotations

from typing import Any, Dict

import oslo_messaging
from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)

_CONF_INITIALIZED = False


def _init_conf() -> None:
    global _CONF_INITIALIZED

    if _CONF_INITIALIZED:
        return

    CONF(
        args=[],
        project="cinder",
        default_config_files=["/etc/cinder/cinder.conf"],
    )

    _CONF_INITIALIZED = True

    LOG.info("RPC configuration loaded from /etc/cinder/cinder.conf")


class SchedulerMetricsAPI:
    RPC_API_VERSION = "1.0"

    def __init__(self) -> None:
        LOG.info("Initializing SchedulerMetricsAPI")

        _init_conf()

        target = oslo_messaging.Target(
            topic="scheduler_metrics",
            version=self.RPC_API_VERSION,
        )

        transport = oslo_messaging.get_rpc_transport(CONF)
        self.client = oslo_messaging.get_rpc_client(transport, target)

        LOG.info(
            "SchedulerMetricsAPI initialized with topic='%s', version='%s'",
            target.topic,
            target.version,
        )

    def push_backend_metrics(self, context: Any, metrics: Dict[str, Any]) -> None:
        LOG.info(
            "Sending backend metrics to scheduler for backend '%s'",
            metrics.get("backend"),
        )

        LOG.debug("Metrics payload: %s", metrics)

        try:
            cctxt = self.client.prepare()
            cctxt.cast(context, "update_backend_metrics", metrics=metrics)

            LOG.info(
                "Metrics sent successfully for backend '%s'",
                metrics.get("backend"),
            )

        except Exception:
            LOG.exception(
                "Failed to send metrics for backend '%s'",
                metrics.get("backend"),
            )
            raise