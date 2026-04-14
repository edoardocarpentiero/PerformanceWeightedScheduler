#!/bin/bash

echo ">>> [PLUGIN] CINDER-COMPLIANCE avviato (fase: $1 / $2)"

function install_cinder_compliance {
    echo ">>> [PLUGIN] FASE INSTALL: copia di performance_weigher.py"

    local SOURCE="/opt/stack/cinder-compliance/devstack/script_scheduler/performance_weigher.py"
    local TARGET_DIR="/opt/stack/cinder/cinder/scheduler/weights"
    local TARGET_FILE="${TARGET_DIR}/performance_weigher.py"

    echo ">>> [PLUGIN] SOURCE: ${SOURCE}"
    echo ">>> [PLUGIN] TARGET: ${TARGET_FILE}"

    if [[ ! -f "$SOURCE" ]]; then
        echo ">>> [PLUGIN][ERRORE] File sorgente non trovato: ${SOURCE}"
        return 1
    fi

    if [[ ! -d "$TARGET_DIR" ]]; then
        echo ">>> [PLUGIN][ERRORE] Directory target non trovata: ${TARGET_DIR}"
        return 1
    fi

    if cp "$SOURCE" "$TARGET_FILE"; then
        echo ">>> [PLUGIN] OK: file copiato correttamente in ${TARGET_FILE}"
    else
        echo ">>> [PLUGIN][ERRORE] Copia fallita verso ${TARGET_FILE}"
        return 1
    fi
}

function configure_cinder_compliance {
    echo ">>> [PLUGIN] FASE POST-CONFIG: aggiornamento cinder.conf"

    local CONF="/etc/cinder/cinder.conf"
    local WEIGHERS="cinder.scheduler.weights.capacity.CapacityWeigher,cinder.scheduler.weights.performance_weigher.PerformanceWeigher"

    echo ">>> [PLUGIN] CONF: ${CONF}"
    echo ">>> [PLUGIN] scheduler_weight_classes: ${WEIGHERS}"

    if [[ ! -f "$CONF" ]]; then
        echo ">>> [PLUGIN][ERRORE] File di configurazione non trovato: ${CONF}"
        return 1
    fi

    if iniset "$CONF" DEFAULT scheduler_weight_classes "$WEIGHERS"; then
        echo ">>> [PLUGIN] OK: scheduler_weight_classes aggiornato"
    else
        echo ">>> [PLUGIN][ERRORE] Aggiornamento di ${CONF} fallito"
        return 1
    fi

    if iniset "$CONF" DEFAULT debug True; then
        echo ">>> [PLUGIN] OK: debug abilitato in cinder.conf"
    else
        echo ">>> [PLUGIN][ERRORE] Impossibile abilitare debug in ${CONF}"
        return 1
    fi
}

if [[ "$1" == "stack" && "$2" == "install" ]]; then
    install_cinder_compliance
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_cinder_compliance
fi