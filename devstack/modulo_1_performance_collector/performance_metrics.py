from __future__ import annotations

import json
import subprocess
import time
from typing import Any, Dict


class PerformanceMetricsCollector:
    """Raccoglie metriche prestazionali dei backend tramite iostat."""

    def collect_iostat_metrics(
        self,
        backend_name: str,
        storage_type_plugin: str,
        device_name: str,
    ) -> Dict[str, Any]:
        print(
            f"[DEBUG][performance_metrics] Avvio raccolta iostat per "
            f"backend='{backend_name}', storage_type='{storage_type_plugin}', "
            f"device='{device_name}'",
            flush=True,
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

        print(
            f"[DEBUG][performance_metrics] Esecuzione comando: {' '.join(cmd)}",
            flush=True,
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            print(
                f"[DEBUG][performance_metrics] stdout di iostat: {result.stdout}",
                flush=True,
            )
            print(
                f"[DEBUG][performance_metrics] stderr di iostat: {result.stderr}",
                flush=True,
            )

            data = json.loads(result.stdout)
            stats = data["sysstat"]["hosts"][0]["statistics"][-1]["disk"]

            disk_stats = None
            for item in stats:
                if item.get("disk_device") == device_name:
                    disk_stats = item
                    break

            if disk_stats is None:
                raise RuntimeError(f"Dispositivo '{device_name}' non trovato nell'output di iostat")

            reads_per_sec = float(disk_stats.get("r/s", 0) or 0)
            writes_per_sec = float(disk_stats.get("w/s", 0) or 0)

            read_kb_s = float(disk_stats.get("rkB/s", 0) or 0)
            write_kb_s = float(disk_stats.get("wkB/s", 0) or 0)
            util_pct = float(disk_stats.get("util", 0) or 0)

            r_await = float(disk_stats.get("r_await", 0) or 0)
            w_await = float(disk_stats.get("w_await", 0) or 0)

            total_ops = reads_per_sec + writes_per_sec

            if total_ops > 0:
                await_ms = (
                    (r_await * reads_per_sec)
                    + (w_await * writes_per_sec)
                ) / total_ops
            else:
                await_ms = 0.0

            metrics = {
                "backend": backend_name,
                "storage_type_plugin": storage_type_plugin,
                "device_name": device_name,
                "iops": reads_per_sec + writes_per_sec,
                "latency_ms": await_ms,
                "throughput_kb_s": read_kb_s + write_kb_s,
                "saturation_pct": util_pct,
            }

            print(
                f"[DEBUG][performance_metrics] Metriche raccolte per il backend "
                f"'{backend_name}': {metrics}",
                flush=True,
            )
            return metrics

        except subprocess.CalledProcessError as exc:
            print(
                f"[ERROR][performance_metrics] Esecuzione di iostat non riuscita per il backend "
                f"'{backend_name}': {exc}",
                flush=True,
            )
            raise
        except Exception as exc:
            print(
                f"[ERROR][performance_metrics] Errore imprevisto durante la raccolta iostat "
                f"per il backend '{backend_name}': {exc}",
                flush=True,
            )
            raise