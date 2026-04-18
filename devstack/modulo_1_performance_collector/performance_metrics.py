from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Dict

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class PerformanceMetricsCollector:
    """Raccoglie metriche prestazionali dei backend tramite fio."""

    def collect_fio_metrics(self, backend_name: str, storage_type: str, test_path: str) -> Dict[str, Any]:
        LOG.info(
            "Starting fio benchmark for backend='%s', storage_type='%s', test_path='%s'",
            backend_name,
            storage_type,
            test_path,
        )

        cmd = [
            "fio",
            "--name=backend_test",
            f"--filename={test_path}",
            "--rw=randread",
            "--bs=4k",
            "--size=1G",
            "--iodepth=32",
            "--runtime=10",
            "--time_based",
            "--direct=1",
            "--ioengine=libaio",
            "--output-format=json",
        ]

        LOG.debug("Executing fio command: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            LOG.debug("fio stdout: %s", result.stdout)

            data = json.loads(result.stdout)
            job = data["jobs"][0]
            read_stats = job["read"]

            latency_ns = read_stats.get("clat_ns", {}).get("mean", 0) or 0
            latency_ms = round(float(latency_ns) / 1_000_000, 3)
            throughput_mb_s = round(
                float(read_stats.get("bw_bytes", 0) or 0) / (1024 * 1024),
                3,
            )

            metrics = {
                "backend": backend_name,
                "storage_type": storage_type,
                "iops": float(read_stats.get("iops", 0) or 0),
                "latency_ms": latency_ms,
                "throughput_mb_s": throughput_mb_s,
                "updated_at": time.time(),
            }

            LOG.info("fio benchmark completed successfully for backend '%s'", backend_name)
            LOG.info("Collected metrics: %s", metrics)

            return metrics

        except subprocess.CalledProcessError:
            LOG.exception("fio execution failed for backend '%s'", backend_name)
            raise
        except Exception:
            LOG.exception("Unexpected error during fio benchmark for backend '%s'", backend_name)
            raise