from __future__ import annotations

from typing import Any, Dict, List

from oslo_config import cfg
from oslo_log import log as logging

from cinder.volume.performance_metrics import PerformanceMetricsCollector
from cinder.volume.scheduler_rpc_api import SchedulerMetricsAPI

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PerformanceCollectorService:
    def __init__(self) -> None:
        LOG.info("Initializing PerformanceCollectorService")
        self.collector = PerformanceMetricsCollector()
        self.rpc_api = SchedulerMetricsAPI()

    def _load_backends_from_conf(self) -> List[Dict[str, Any]]:
        LOG.info("Loading backend configuration from cinder.conf")

        backends: List[Dict[str, Any]] = []

        enabled_backends = getattr(CONF, "enabled_backends", None)
        if not enabled_backends:
            LOG.warning("No enabled_backends configured in cinder.conf")
            return backends

        if isinstance(enabled_backends, str):
            enabled_backends = [b.strip() for b in enabled_backends.split(",") if b.strip()]

        LOG.info("Detected enabled backends: %s", enabled_backends)

        for backend_section in enabled_backends:
            LOG.info("Processing backend section: %s", backend_section)

            group = getattr(CONF, backend_section, None)
            if group is None:
                LOG.warning("Backend section '%s' not found in CONF", backend_section)
                continue

            backend_name = getattr(group, "volume_backend_name", backend_section)
            storage_type = getattr(group, "storage_type", "LVM")
            test_path = getattr(group, "fio_path", None)
            performance_index = getattr(group, "my_custom_performance_index", 0)

            if not test_path:
                volume_group = getattr(group, "volume_group", None)
                if volume_group:
                    test_path = f"/dev/{volume_group}/fio_test_lv"
                    LOG.info(
                        "Backend '%s': using derived fio path '%s' from volume_group '%s'",
                        backend_name,
                        test_path,
                        volume_group,
                    )
                else:
                    test_path = f"/tmp/{backend_section}_fio_testfile"
                    LOG.info(
                        "Backend '%s': using fallback fio path '%s'",
                        backend_name,
                        test_path,
                    )

            backend_info = {
                "backend": backend_name,
                "storage_type": storage_type,
                "test_path": test_path,
                "performance_index": performance_index,
                "backend_section": backend_section,
            }

            LOG.info("Backend configuration loaded: %s", backend_info)
            backends.append(backend_info)

        LOG.info("Loaded %d backend configurations", len(backends))
        return backends

    def publish_all_backend_metrics(self, context: Any, backends: List[Dict[str, Any]]) -> None:
        LOG.info("Publishing metrics for %d backends", len(backends))

        for backend in backends:
            backend_name = backend["backend"]
            LOG.info("Collecting metrics for backend '%s'", backend_name)

            try:
                metrics = self.collector.collect_fio_metrics(
                    backend_name=backend["backend"],
                    storage_type=backend["storage_type"],
                    test_path=backend["test_path"],
                )

                metrics["performance_index"] = backend.get("performance_index", 0)
                metrics["backend_section"] = backend.get("backend_section")

                LOG.info("Collected metrics for backend '%s': %s", backend_name, metrics)

                self.rpc_api.push_backend_metrics(context, metrics)

                LOG.info("Metrics published successfully for backend '%s'", backend_name)

            except Exception:
                LOG.exception("Failed to collect/publish metrics for backend '%s'", backend_name)

    def update_all_backend_metrics(self, context: Any) -> None:
        LOG.info("Starting update_all_backend_metrics")

        backends = self._load_backends_from_conf()
        self.publish_all_backend_metrics(context, backends)

        LOG.info("Completed update_all_backend_metrics")

    def get_backend_metrics(
        self,
        backend_name: str,
        storage_type: str,
        test_path: str,
    ) -> Dict[str, Any]:
        LOG.info(
            "Fetching on-demand metrics for backend='%s', storage_type='%s', test_path='%s'",
            backend_name,
            storage_type,
            test_path,
        )

        metrics = self.collector.collect_fio_metrics(
            backend_name=backend_name,
            storage_type=storage_type,
            test_path=test_path,
        )

        LOG.info("On-demand metrics collected for backend '%s': %s", backend_name, metrics)
        return metrics