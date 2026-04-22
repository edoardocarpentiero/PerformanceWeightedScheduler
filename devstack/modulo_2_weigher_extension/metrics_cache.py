from __future__ import annotations

from typing import Any, Dict, Optional
import threading
import time


class BackendMetricsCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._ttl_seconds = ttl_seconds

        print(
            f"[DEBUG][metrics_cache] Cache inizializzata con TTL={ttl_seconds} secondi",
            flush=True,
        )

    def put(self, backend_name: str, metrics: Dict[str, Any]) -> None:
        with self._lock:
            print(
                f"[DEBUG][metrics_cache] Inserimento metriche per backend '{backend_name}'",
                flush=True,
            )
            self._data[backend_name] = metrics

    def get(self, backend_name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            metrics = self._data.get(backend_name)

            print(
                f"[DEBUG][metrics_cache] Recupero metriche per backend '{backend_name}': {metrics}",
                flush=True,
            )

            return metrics

    def is_stale(self, backend_name: str) -> bool:
        with self._lock:
            metrics = self._data.get(backend_name)

            if not metrics:
                print(
                    f"[DEBUG][metrics_cache] Metriche assenti per backend '{backend_name}'",
                    flush=True,
                )
                return True

            updated_at = metrics.get("updated_at")

            if updated_at is None:
                print(
                    f"[DEBUG][metrics_cache] Timestamp mancante per backend '{backend_name}'",
                    flush=True,
                )
                return True

            stale = (time.time() - float(updated_at)) > self._ttl_seconds

            print(
                f"[DEBUG][metrics_cache] Verifica stale backend '{backend_name}': {stale}",
                flush=True,
            )

            return stale