from __future__ import annotations

import configparser
import logging
import signal
import sys
import time

print("[DEBUG] modulo collector_daemon importato", flush=True)

from cinder import context as cinder_context
from cinder.volume.performance_weighted_scheduler_module1.collector_service import (
    PerformanceCollectorService,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

LOG = logging.getLogger(__name__)

CINDER_CONF_PATH = "/etc/cinder/cinder.conf"
_SHOULD_STOP = False


def _handle_signal(signum, frame) -> None:
    global _SHOULD_STOP
    print(f"[DEBUG] ricevuto segnale {signum}", flush=True)
    LOG.info("Ricevuto segnale %s, arresto del daemon collector in corso", signum)
    _SHOULD_STOP = True


def _load_interval_from_conf(conf_path: str) -> int:
    print(f"[DEBUG] caricamento intervallo da conf_path='{conf_path}'", flush=True)

    parser = configparser.ConfigParser(interpolation=None)
    read_files = parser.read(conf_path)

    print(f"[DEBUG] parser.read ha restituito: {read_files}", flush=True)

    if not read_files:
        print(
            f"[DEBUG] Impossibile leggere '{conf_path}', "
            f"uso il valore predefinito performance_collector_interval=30: {read_files}",
            flush=True,
        )
        return 30

    value = parser.get("DEFAULT", "performance_collector_interval", fallback="30")

    print(f"[DEBUG] valore grezzo di performance_collector_interval='{value}'", flush=True)

    try:
        interval = int(value)

        if interval <= 0:
            raise ValueError("L'intervallo deve essere positivo")

        print(f"[DEBUG] intervallo interpretato={interval}", flush=True)
        return interval

    except Exception as exc:
        print(f"[DEBUG] errore durante l'interpretazione dell'intervallo: {exc}", flush=True)

        return 30


def main() -> int:
    global _SHOULD_STOP

    print("[DEBUG] ingresso in main()", flush=True)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print("[DEBUG] gestori dei segnali registrati", flush=True)

    interval = _load_interval_from_conf(CINDER_CONF_PATH)

    print(f"[DEBUG] intervallo caricato: {interval}", flush=True)

    print(
        f"[DEBUG] Avvio del daemon Performance Collector con intervallo={interval} secondi, "
        f"conf_path='{CINDER_CONF_PATH}'",
        flush=True,
    )

    collector = PerformanceCollectorService(conf_path=CINDER_CONF_PATH)

    print("[DEBUG] PerformanceCollectorService creato", flush=True)

    admin_context = cinder_context.get_admin_context()

    print("[DEBUG] admin_context creato", flush=True)

    while not _SHOULD_STOP:
        try:
            print("[DEBUG] avvio ciclo periodico di raccolta", flush=True)

            collector.update_all_backend_metrics(admin_context)

            print("[DEBUG] ciclo periodico di raccolta completato", flush=True)

        except Exception as exc:
            print(f"[DEBUG] raccolta periodica non riuscita: {exc}", flush=True)
            LOG.exception("Raccolta periodica delle metriche non riuscita")

        if _SHOULD_STOP:
            print("[DEBUG] flag di arresto rilevato, uscita dal ciclo", flush=True)
            break

        print(f"[DEBUG] sospensione per {interval} secondi", flush=True)
        time.sleep(interval)

    print("[DEBUG] daemon collector arrestato", flush=True)

    return 0


if __name__ == "__main__":
    try:
        print("[DEBUG] entrypoint __main__ raggiunto", flush=True)
        sys.exit(main())
    except Exception as exc:
        import traceback

        print(f"[FATAL] arresto anomalo del daemon collector: {exc}", flush=True)
        traceback.print_exc()
        raise