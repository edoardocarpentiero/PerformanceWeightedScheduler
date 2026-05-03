from __future__ import annotations

import configparser
import subprocess
from typing import Any, Dict, List, Optional

from cinder import context as cinder_context

from cinder.volume.performance_weighted_scheduler_module1.performance_metrics import (
    PerformanceMetricsCollector,
)
from cinder.volume.performance_weighted_scheduler_module1.scheduler_rpc_api import (
    SchedulerMetricsAPI,
)

CINDER_CONF_PATH = "/etc/cinder/cinder.conf"


class PerformanceCollectorService:
    def __init__(self, conf_path: str = CINDER_CONF_PATH) -> None:
        print(
            f"[DEBUG][collector_service] Inizializzazione di PerformanceCollectorService "
            f"con conf_path='{conf_path}'",
            flush=True,
        )
        self.conf_path = conf_path
        self.collector = PerformanceMetricsCollector()
        print("[DEBUG][collector_service] PerformanceMetricsCollector creato", flush=True)
        self.rpc_api = SchedulerMetricsAPI()
        print("[DEBUG][collector_service] SchedulerMetricsAPI creato", flush=True)

    def _load_parser(self) -> configparser.ConfigParser:
        print(
            f"[DEBUG][collector_service] Caricamento del parser per '{self.conf_path}'",
            flush=True,
        )

        parser = configparser.ConfigParser(interpolation=None)
        read_files = parser.read(self.conf_path)

        print(
            f"[DEBUG][collector_service] parser.read ha restituito: {read_files}",
            flush=True,
        )

        if not read_files:
            raise RuntimeError(f"Impossibile leggere il file di configurazione: {self.conf_path}")

        print(
            f"[DEBUG][collector_service] Configurazione caricata correttamente da "
            f"'{self.conf_path}'",
            flush=True,
        )
        return parser

    def _resolve_iostat_device_from_vg(self, volume_group: str) -> Optional[str]:
        try:
            print(
                f"[DEBUG][collector_service] Risoluzione del dispositivo iostat da "
                f"volume_group='{volume_group}'",
                flush=True,
            )

            cmd = [
                "sudo",
                "vgs",
                "--noheadings",
                "-o",
                "pv_name",
                volume_group,
            ]

            print(
                f"[DEBUG][collector_service] Esecuzione comando: {' '.join(cmd)}",
                flush=True,
            )

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
            )

            print(
                f"[DEBUG][collector_service] stdout di vgs: {result.stdout}",
                flush=True,
            )
            print(
                f"[DEBUG][collector_service] stderr di vgs: {result.stderr}",
                flush=True,
            )

            pv_name = result.stdout.strip()

            if not pv_name:
                print(
                    f"[WARN][collector_service] Nessun volume fisico trovato per "
                    f"volume_group='{volume_group}'",
                    flush=True,
                )
                return None

            pv_name = pv_name.splitlines()[0].strip()
            device_name = pv_name.split("/")[-1]

            print(
                f"[DEBUG][collector_service] Risolto volume_group='{volume_group}' "
                f"in device_name='{device_name}' usando pv_name='{pv_name}'",
                flush=True,
            )

            return device_name

        except Exception as exc:
            print(
                f"[ERROR][collector_service] Impossibile risolvere il dispositivo iostat da "
                f"volume_group='{volume_group}': {exc}",
                flush=True,
            )
            return None

    def _load_backends_from_conf(self) -> List[Dict[str, Any]]:
        print(
            f"[DEBUG][collector_service] Caricamento della configurazione dei backend da "
            f"'{self.conf_path}'",
            flush=True,
        )

        parser = self._load_parser()
        backends: List[Dict[str, Any]] = []

        enabled_backends_raw = parser.get("DEFAULT", "enabled_backends", fallback="")
        print(
            f"[DEBUG][collector_service] enabled_backends grezzo='{enabled_backends_raw}'",
            flush=True,
        )

        if not enabled_backends_raw.strip():
            print(
                f"[WARN][collector_service] Nessun enabled_backends configurato in "
                f"'{self.conf_path}'",
                flush=True,
            )
            return backends

        enabled_backends = [
            b.strip() for b in enabled_backends_raw.split(",") if b.strip()
        ]

        print(
            f"[DEBUG][collector_service] enabled_backends interpretati={enabled_backends}",
            flush=True,
        )

        for backend_section in enabled_backends:
            print(
                f"[DEBUG][collector_service] Elaborazione backend_section="
                f"'{backend_section}'",
                flush=True,
            )

            if not parser.has_section(backend_section):
                print(
                    f"[WARN][collector_service] Sezione backend '{backend_section}' "
                    f"non trovata in '{self.conf_path}'",
                    flush=True,
                )
                continue

            backend_conf = dict(parser.items(backend_section))
            print(
                f"[DEBUG][collector_service] backend_conf[{backend_section}]="
                f"{backend_conf}",
                flush=True,
            )

            backend_name = backend_conf.get("volume_backend_name", backend_section)
            storage_type_plugin = backend_conf.get("storage_type_plugin", "LVM")
            device_name = backend_conf.get("iostat_device")
            volume_group = backend_conf.get("volume_group")

            print(
                f"[DEBUG][collector_service] backend_name='{backend_name}', "
                f"storage_type_plugin='{storage_type_plugin}', device_name='{device_name}', "
                f"volume_group='{volume_group}'",
                flush=True,
            )

            if device_name:
                print(
                    f"[DEBUG][collector_service] Uso iostat_device configurato "
                    f"'{device_name}' per il backend '{backend_name}'",
                    flush=True,
                )
            else:
                if volume_group:
                    device_name = self._resolve_iostat_device_from_vg(volume_group)

                if not device_name:
                    print(
                        f"[WARN][collector_service] Backend '{backend_name}': "
                        f"impossibile determinare automaticamente il dispositivo iostat; backend saltato",
                        flush=True,
                    )
                    continue

            backend_info = {
                "backend": backend_name,
                "storage_type_plugin": storage_type_plugin,
                "device_name": device_name,
                "backend_section": backend_section,
            }

            print(
                f"[DEBUG][collector_service] backend_info={backend_info}",
                flush=True,
            )
            backends.append(backend_info)

        print(
            f"[DEBUG][collector_service] Caricate {len(backends)} configurazioni backend",
            flush=True,
        )
        return backends

    def publish_all_backend_metrics(self, context: Any, backends: List[Dict[str, Any]]) -> None:
        print(
            f"[DEBUG][collector_service] Pubblicazione metriche per {len(backends)} backend",
            flush=True,
        )

        for backend in backends:
            backend_name = backend["backend"]
            print(
                f"[DEBUG][collector_service] Raccolta metriche per il backend "
                f"'{backend_name}'",
                flush=True,
            )

            try:
                metrics = self.collector.collect_iostat_metrics(
                    backend_name=backend["backend"],
                    storage_type_plugin=backend["storage_type_plugin"],
                    device_name=backend["device_name"],
                )

                metrics["backend_section"] = backend.get("backend_section")

                print(
                    f"[DEBUG][collector_service] metriche per il backend "
                    f"'{backend_name}' = {metrics}",
                    flush=True,
                )

                self.rpc_api.push_backend_metrics(context, metrics)

                print(
                    f"[DEBUG][collector_service] Metriche pubblicate correttamente per "
                    f"il backend '{backend_name}'",
                    flush=True,
                )

            except Exception as exc:
                print(
                    f"[ERROR][collector_service] Impossibile raccogliere/pubblicare le metriche "
                    f"per il backend '{backend_name}': {exc}",
                    flush=True,
                )

    def update_all_backend_metrics(self, context: Any | None = None) -> None:
        print("[DEBUG][collector_service] Avvio di update_all_backend_metrics", flush=True)

        if context is None:
            print(
                "[DEBUG][collector_service] Nessun context fornito, creazione di admin_context",
                flush=True,
            )
            context = cinder_context.get_admin_context()

        backends = self._load_backends_from_conf()
        self.publish_all_backend_metrics(context, backends)

        print("[DEBUG][collector_service] Completato update_all_backend_metrics", flush=True)

    def get_backend_metrics(
        self,
        backend_name: str,
        storage_type_plugin: str,
        device_name: str,
    ) -> Dict[str, Any]:
        print(
            f"[DEBUG][collector_service] Recupero metriche su richiesta per "
            f"backend='{backend_name}', storage_type_plugin='{storage_type_plugin}', "
            f"device_name='{device_name}'",
            flush=True,
        )

        metrics = self.collector.collect_iostat_metrics(
            backend_name=backend_name,
            storage_type_plugin=storage_type_plugin,
            device_name=device_name,
        )

        print(
            f"[DEBUG][collector_service] Metriche su richiesta raccolte per il backend "
            f"'{backend_name}': {metrics}",
            flush=True,
        )
        return metrics