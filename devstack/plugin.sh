#!/bin/bash
set -x

echo ">>> [PLUGIN] fase: $1 / $2"

install_fio() {
    echo ">>> [PLUGIN] Installazione fio"

    if command -v fio >/dev/null 2>&1; then
        echo ">>> [PLUGIN] fio già installato"
    else
        sudo apt-get update
        sudo apt-get install -y fio || return 1
        echo ">>> [PLUGIN] fio installato correttamente"
    fi
}
patch_volume_manager() {
    local PATCH_SCRIPT="/opt/stack/cinder-compliance/devstack/patch_volume_manager.py"

    echo ">>> [PLUGIN] Patch di manager.py"
    echo ">>> [PLUGIN] PATCH_SCRIPT = $PATCH_SCRIPT"

    [[ -f "$PATCH_SCRIPT" ]] || { echo ">>> [PLUGIN][ERRORE] Script patch non trovato: $PATCH_SCRIPT"; return 1; }

    python3 "$PATCH_SCRIPT" || return 1

    echo ">>> [PLUGIN] Patch manager.py completata"
}

install_performance_collector() {
    local SRC_DIR="/opt/stack/cinder-compliance/devstack/modulo_1_performance_collector"
    local DST_DIR="/opt/stack/cinder/cinder/volume"

    echo ">>> [PLUGIN] Installazione Modulo 1 - Performance Collector"
    echo ">>> [PLUGIN] SRC_DIR = $SRC_DIR"
    echo ">>> [PLUGIN] DST_DIR = $DST_DIR"

    [[ -d "$SRC_DIR" ]] || { echo ">>> [PLUGIN][ERRORE] Directory sorgente non trovata: $SRC_DIR"; return 1; }
    [[ -d "$DST_DIR" ]] || { echo ">>> [PLUGIN][ERRORE] Directory target non trovata: $DST_DIR"; return 1; }

    cp "${SRC_DIR}"/*.py "$DST_DIR"/ || return 1

    echo ">>> [PLUGIN] Modulo 1 copiato correttamente"
}

install_weigher_extension() {
    local SRC="/opt/stack/cinder-compliance/devstack/modulo_2_weigher_extension/performance_weigher.py"
    local DST="/opt/stack/cinder/cinder/scheduler/weights/performance_weigher.py"
    local CINDER_DIR="/opt/stack/cinder"
    local PYPROJECT="${CINDER_DIR}/pyproject.toml"
    local ENTRY='PerformanceWeigher = "cinder.scheduler.weights.performance_weigher:PerformanceWeigher"'

    echo ">>> [PLUGIN] Installazione Modulo 2 - Weigher Extension"
    echo ">>> [PLUGIN] SRC = $SRC"
    echo ">>> [PLUGIN] DST = $DST"

    [[ -f "$SRC" ]] || { echo ">>> [PLUGIN][ERRORE] File sorgente non trovato: $SRC"; return 1; }
    [[ -f "$PYPROJECT" ]] || { echo ">>> [PLUGIN][ERRORE] pyproject.toml non trovato: $PYPROJECT"; return 1; }

    cp "$SRC" "$DST" || return 1

    echo ">>> [PLUGIN] Verifica entry point in pyproject.toml"

    if grep -qF "$ENTRY" "$PYPROJECT"; then
        echo ">>> [PLUGIN] Entry già presente"
    else
        echo ">>> [PLUGIN] Aggiungo entry point"
        sed -i '/^\[project.entry-points."cinder.scheduler.weights"\]/a\
'"$ENTRY"'' "$PYPROJECT" || return 1
    fi

    echo ">>> [PLUGIN] Reinstallazione editable di Cinder"
    (cd "$CINDER_DIR" && python3 -m pip install --break-system-packages -e .) || return 1

    echo ">>> [PLUGIN] Modulo 2 installato correttamente"
}

configure_performance_collector() {
    local CONF="/etc/cinder/cinder.conf"

    echo ">>> [PLUGIN] Configurazione Modulo 1 - Performance Collector"
    echo ">>> [PLUGIN] CONF = $CONF"

    [[ -f "$CONF" ]] || { echo ">>> [PLUGIN][ERRORE] File di configurazione non trovato: $CONF"; return 1; }

    iniset "$CONF" DEFAULT debug True || return 1

    echo ">>> [PLUGIN] debug = True"
}

configure_weigher_extension() {
    local CONF="/etc/cinder/cinder.conf"

    echo ">>> [PLUGIN] Configurazione Modulo 2 - Weigher Extension"
    echo ">>> [PLUGIN] CONF = $CONF"

    [[ -f "$CONF" ]] || { echo ">>> [PLUGIN][ERRORE] File di configurazione non trovato: $CONF"; return 1; }

    iniset "$CONF" DEFAULT scheduler_default_weighers PerformanceWeigher || return 1

    echo ">>> [PLUGIN] scheduler_default_weighers = PerformanceWeigher"
}

if [[ "$1" == "stack" && "$2" == "install" ]]; then
    install_fio || exit 1
    install_performance_collector || exit 1
    install_weigher_extension || exit 1
	patch_volume_manager || exit 1
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_performance_collector || exit 1
    configure_weigher_extension || exit 1
fi