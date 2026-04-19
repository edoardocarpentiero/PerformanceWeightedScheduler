from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Dict

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class PerformanceMetricsCollector:
    """Raccoglie metriche prestazionali dei backend tramite iostat."""

    def collect_iostat_metrics(
        self,
        backend_name: str,
        storage_type: str,
        device_name: str,
    ) -> Dict[str, Any]:
        LOG.info(
            "Starting iostat collection for backend='%s', storage_type='%s', device='%s'",
            backend_name,
            storage_type,
            device_name,
        )

        cmd = [
            "iostat",
            "-dx",
            "-y",
            "-o", "JSON",
            device_name,
            "1",
            "2",
        ]

        LOG.debug("Executing iostat command: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            LOG.debug("iostat stdout: %s", result.stdout)

            data = json.loads(result.stdout)
            stats = data["sysstat"]["hosts"][0]["statistics"][-1]["disk"]

            disk_stats = None
            for item in stats:
                if item.get("disk_device") == device_name:
                    disk_stats = item
                    break

            if disk_stats is None:
                raise RuntimeError(f"Device '{device_name}' not found in iostat output")

            reads_per_sec = float(disk_stats.get("r/s", 0) or 0)
            writes_per_sec = float(disk_stats.get("w/s", 0) or 0)
            read_kb_s = float(disk_stats.get("rkB/s", 0) or 0)
            write_kb_s = float(disk_stats.get("wkB/s", 0) or 0)
            await_ms = float(disk_stats.get("await", 0) or 0)
            util_pct = float(disk_stats.get("%util", 0) or 0)

            metrics = {
                "backend": backend_name,
                "storage_type": storage_type,
                "device_name": device_name,
                "iops": reads_per_sec + writes_per_sec,
                "latency_ms": await_ms,
                "throughput_kb_s": read_kb_s + write_kb_s,
                "saturation_pct": util_pct,
                "updated_at": time.time(),
            }

            LOG.info("iostat collection completed successfully for backend '%s'", backend_name)
            LOG.info("Collected metrics: %s", metrics)

            return metrics

        except subprocess.CalledProcessError:
            LOG.exception("iostat execution failed for backend '%s'", backend_name)
            raise
        except Exception:
            LOG.exception("Unexpected error during iostat collection for backend '%s'", backend_name)
            raise