from __future__ import annotations

import configparser
import signal
import sys
import time

from oslo_log import log as logging

from cinder import context as cinder_context
from cinder.volume.performance_weighted_scheduler_module1.collector_service import (
    PerformanceCollectorService,
)

LOG = logging.getLogger(__name__)

CINDER_CONF_PATH = "/etc/cinder/cinder.conf"
_SHOULD_STOP = False


def _handle_signal(signum, frame) -> None:
    global _SHOULD_STOP
    LOG.info("Received signal %s, stopping collector daemon", signum)
    _SHOULD_STOP = True


def _load_interval_from_conf(conf_path: str) -> int:
    parser = configparser.ConfigParser()
    read_files = parser.read(conf_path)

    if not read_files:
        LOG.warning(
            "Unable to read '%s', using default performance_collector_interval=30",
            conf_path,
        )
        return 30

    value = parser.get("DEFAULT", "performance_collector_interval", fallback="30")

    try:
        interval = int(value)
        if interval <= 0:
            raise ValueError("Interval must be positive")
        return interval
    except Exception:
        LOG.warning(
            "Invalid performance_collector_interval='%s' in '%s', using default 30",
            value,
            conf_path,
        )
        return 30


def main() -> int:
    global _SHOULD_STOP

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    interval = _load_interval_from_conf(CINDER_CONF_PATH)

    LOG.info(
        "Starting Performance Collector daemon with interval=%s seconds, conf_path='%s'",
        interval,
        CINDER_CONF_PATH,
    )

    collector = PerformanceCollectorService(conf_path=CINDER_CONF_PATH)
    admin_context = cinder_context.get_admin_context()

    while not _SHOULD_STOP:
        try:
            collector.update_all_backend_metrics(admin_context)
        except Exception:
            LOG.exception("Periodic metrics collection failed")

        if _SHOULD_STOP:
            break

        time.sleep(interval)

    LOG.info("Performance Collector daemon stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
