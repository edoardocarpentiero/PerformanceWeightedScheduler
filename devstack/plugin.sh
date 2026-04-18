#!/bin/bash
set -x

echo ">>> [PLUGIN] fase: $1 / $2"

install_cinder_compliance() {
    local SRC="/opt/stack/cinder-compliance/devstack/modulo_1_performance_collector/performance_weigher.py"
    local DST="/opt/stack/cinder/cinder/scheduler/weights/performance_weigher.py"
    local CINDER_DIR="/opt/stack/cinder"
    local PYPROJECT="${CINDER_DIR}/pyproject.toml"
    local ENTRY='PerformanceWeigher = "cinder.scheduler.weights.performance_weigher:PerformanceWeigher"'

    echo ">>> [PLUGIN] Copia file:"
    echo ">>> [PLUGIN] SRC = $SRC"
    echo ">>> [PLUGIN] DST = $DST"

    cp "$SRC" "$DST" || return 1

    echo ">>> [PLUGIN] File copiato"

    echo ">>> [PLUGIN] Verifica entry point in pyproject.toml"

    if grep -qF "$ENTRY" "$PYPROJECT"; then
        echo ">>> [PLUGIN] Entry già presente"
    else
        echo ">>> [PLUGIN] Aggiungo entry:"
        echo ">>> [PLUGIN] $ENTRY"

        sed -i '/^\[project.entry-points."cinder.scheduler.weights"\]/a\
'"$ENTRY"'' "$PYPROJECT" || return 1

        echo ">>> [PLUGIN] Entry aggiunta"
    fi

    echo ">>> [PLUGIN] Reinstallazione editable di Cinder"

    (cd "$CINDER_DIR" && python3 -m pip install --break-system-packages -e .) || return 1

    echo ">>> [PLUGIN] Reinstallazione completata"
}

configure_cinder_compliance() {
    local CONF="/etc/cinder/cinder.conf"

    echo ">>> [PLUGIN] Configurazione cinder.conf"
    echo ">>> [PLUGIN] CONF = $CONF"

    iniset "$CONF" DEFAULT scheduler_default_weighers PerformanceWeigher
    iniset "$CONF" DEFAULT debug True

    echo ">>> [PLUGIN] scheduler_default_weighers = PerformanceWeigher"
    echo ">>> [PLUGIN] debug = True"
}

if [[ "$1" == "stack" && "$2" == "install" ]]; then
    install_cinder_compliance
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_cinder_compliance
fi