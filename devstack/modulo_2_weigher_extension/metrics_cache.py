from __future__ import annotations

from typing import Any, Dict, Optional
import threading


class BackendMetricsCache:
    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

        print(
            "[DEBUG][metrics_cache] Cache metriche inizializzata",
            flush=True,
        )

    def put(self, backend_name: str, metrics: Dict[str, Any]) -> None:
        with self._lock:
            print(
                f"[DEBUG][metrics_cache] Salvataggio metriche per backend '{backend_name}'",
                flush=True,
            )
            self._data[backend_name] = metrics

    def get(self, backend_name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            metrics = self._data.get(backend_name)

            print(
                f"[DEBUG][metrics_cache] Lettura metriche per backend '{backend_name}': {metrics}",
                flush=True,
            )

            return metrics

    def find_by_host_state(self, host_state_name: str) -> Optional[Dict[str, Any]]:
        """
        Cerca le metriche verificando se il nome del backend presente in cache
        compare dentro host_state.host.

        Esempio:
        - chiave cache: low_cap
        - host_state.host: controller@low_cap#pool
        """
        with self._lock:
            print(
                f"[DEBUG][metrics_cache] Ricerca metriche per host_state '{host_state_name}'",
                flush=True,
            )

            for backend_name, metrics in self._data.items():
                if backend_name in host_state_name:
                    print(
                        f"[DEBUG][metrics_cache] Corrispondenza trovata: "
                        f"backend cache '{backend_name}' presente in host_state '{host_state_name}'",
                        flush=True,
                    )
                    return metrics

            print(
                f"[WARN][metrics_cache] Nessuna metrica trovata per host_state '{host_state_name}'",
                flush=True,
            )
            return None


_CACHE = BackendMetricsCache()


def get_metrics_cache() -> BackendMetricsCache:
    return _CACHE