from __future__ import annotations

import configparser
import logging
import signal
import sys
import time

print("[PLUGIN - MD1] modulo collector_daemon importato", flush=True)

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
    print(f"[PLUGIN - MD1 >> collector_daemon] ricevuto segnale {signum}", flush=True)
    _SHOULD_STOP = True


def caricaIntervalloDaemon(conf_path: str) -> int:
    print(f"[PLUGIN - MD1 >> collector_daemon] caricamento intervallo da conf_path='{conf_path}'", flush=True)

    parser = configparser.ConfigParser(interpolation=None)
    read_files = parser.read(conf_path)

    print(f"[PLUGIN - MD1 >> collector_daemon] parser.read ha restituito: {read_files}", flush=True)

    if not read_files:
        print(
            f"[PLUGIN - MD1 >> collector_daemon] Impossibile leggere '{conf_path}', "
            f"uso il valore predefinito performance_collector_interval=30: {read_files}",
            flush=True,
        )
        return 30

    value = parser.get("DEFAULT", "performance_collector_interval", fallback="30")

    print(f"[PLUGIN - MD1 >> collector_daemon] valore grezzo di performance_collector_interval='{value}'", flush=True)

    try:
        interval = int(value)

        if interval <= 0:
            raise ValueError("L'intervallo deve essere positivo")

        print(f"[PLUGIN - MD1 >> collector_daemon] intervallo interpretato={interval}", flush=True)
        return interval

    except Exception as exc:
        print(f"[PLUGIN - MD1 >> collector_daemon] errore durante l'interpretazione dell'intervallo: {exc}", flush=True)

        return 30


def main() -> int:
    global _SHOULD_STOP

    print("[PLUGIN - MD1 >> collector_daemon] ingresso in main()", flush=True)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    print("[PLUGIN - MD1 >> collector_daemon] gestori dei segnali registrati", flush=True)

    interval = caricaIntervalloDaemon(CINDER_CONF_PATH)

    print(f"[PLUGIN - MD1 >> collector_daemon] intervallo caricato: {interval}", flush=True)

    print(
        f"[PLUGIN - MD1 >> collector_daemon] Avvio del daemon Performance Collector con intervallo={interval} secondi, "
        f"conf_path='{CINDER_CONF_PATH}'",
        flush=True,
    )

    collector = PerformanceCollectorService(conf_path=CINDER_CONF_PATH)

    print("[PLUGIN - MD1 >> collector_daemon] PerformanceCollectorService creato", flush=True)

    admin_context = cinder_context.get_admin_context()

    print("[PLUGIN - MD1 >> collector_daemon] admin_context creato", flush=True)

    while not _SHOULD_STOP:
        try:
            print("[PLUGIN - MD1 >> collector_daemon] avvio ciclo periodico di raccolta", flush=True)

            collector.caricaMetricheBackend(admin_context)

            print("[PLUGIN - MD1 >> collector_daemon] ciclo periodico di raccolta completato", flush=True)

        except Exception as exc:
            print(f"[PLUGIN - MD1 >> collector_daemon] raccolta periodica non riuscita: {exc}", flush=True)

        if _SHOULD_STOP:
            print("[PLUGIN - MD1 >> collector_daemon] flag di arresto rilevato, uscita dal ciclo", flush=True)
            break

        print(f"[PLUGIN - MD1 >> collector_daemon] sospensione per {interval} secondi", flush=True)
        time.sleep(interval)

    print("[PLUGIN - MD1 >> collector_daemon] daemon collector arrestato", flush=True)

    return 0


if __name__ == "__main__":
    try:
        print("[PLUGIN - MD1 >> collector_daemon] entrypoint __main__ raggiunto", flush=True)
        sys.exit(main())
    except Exception as exc:
        import traceback

        print(f"[PLUGIN - MD1 >> collector_daemon] arresto anomalo del daemon collector: {exc}", flush=True)
        traceback.print_exc()
        raise