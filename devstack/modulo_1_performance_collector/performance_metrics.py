"""
Modulo 1 - Performance Collector
Raccoglie metriche dei backend tramite fio e restituisce
un payload strutturato pronto per l'invio via RPC.
"""

from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Dict


class PerformanceMetricsCollector:
    """Raccoglie metriche prestazionali dei backend tramite fio."""

    def collect_fio_metrics(self, backend_name: str, storage_type: str, test_path: str) -> Dict[str, Any]:
        """Esegue fio e restituisce un payload strutturato con le metriche del backend.

        Parametri:
        - backend_name: nome logico del backend
        - storage_type: tipologia di storage (es. SSD/HDD)
        - test_path: percorso del file o device su cui eseguire il benchmark
        """
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

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        job = data["jobs"][0]
        read_stats = job["read"]

        # Conversioni per avere valori più leggibili nel plugin
        latency_ns = read_stats.get("clat_ns", {}).get("mean", 0) or 0
        latency_ms = round(float(latency_ns) / 1_000_000, 3)
        throughput_mb_s = round(float(read_stats.get("bw_bytes", 0) or 0) / (1024 * 1024), 3)

        return {
            "backend": backend_name,
            "storage_type": storage_type,
            "iops": float(read_stats.get("iops", 0) or 0),
            "latency_ms": latency_ms,
            "throughput_mb_s": throughput_mb_s,
            "updated_at": time.time(),
        }
