from __future__ import annotations

from typing import Any, Dict, Optional
import threading
import time


class BackendMetricsCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._ttl_seconds = ttl_seconds

    def put(self, backend_name: str, metrics: Dict[str, Any]) -> None:
        with self._lock:
            self._data[backend_name] = metrics

    def get(self, backend_name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._data.get(backend_name)

    def is_stale(self, backend_name: str) -> bool:
        with self._lock:
            metrics = self._data.get(backend_name)
            if not metrics:
                return True

            updated_at = metrics.get("updated_at")
            if updated_at is None:
                return True

            return (time.time() - float(updated_at)) > self._ttl_seconds
