#!/bin/bash

echo ">>> [PLUGIN] CINDER-COMPLIANCE avviato (fase: $1 / $2)"

function install_cinder_compliance {
    echo ">>> [PLUGIN] FASE INSTALL: copia di performance_weigher.py + registrazione entry point"

    local SOURCE="/opt/stack/cinder-compliance/devstack/script_scheduler/performance_weigher.py"
    local TARGET_DIR="/opt/stack/cinder/cinder/scheduler/weights"
    local TARGET_FILE="${TARGET_DIR}/performance_weigher.py"
    local CINDER_DIR="/opt/stack/cinder"
    local PYPROJECT="${CINDER_DIR}/pyproject.toml"
    local ENTRY='PerformanceWeigher = "cinder.scheduler.weights.performance_weigher:PerformanceWeigher"'

    echo ">>> [PLUGIN] SOURCE: ${SOURCE}"
    echo ">>> [PLUGIN] TARGET: ${TARGET_FILE}"
    echo ">>> [PLUGIN] PYPROJECT: ${PYPROJECT}"

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

    if [[ ! -f "$PYPROJECT" ]]; then
        echo ">>> [PLUGIN][ERRORE] pyproject.toml non trovato: ${PYPROJECT}"
        return 1
    fi

    if grep -qF "$ENTRY" "$PYPROJECT"; then
        echo ">>> [PLUGIN] Entry point già presente in pyproject.toml"
    else
        echo ">>> [PLUGIN] Aggiunta entry point in pyproject.toml"

        if grep -q '^\[project.entry-points."cinder.scheduler.weights"\]' "$PYPROJECT"; then
            sed -i '/^\[project.entry-points."cinder.scheduler.weights"\]/a\
'"$ENTRY"'' "$PYPROJECT"
        else
            cat >> "$PYPROJECT" <<EOF

[project.entry-points."cinder.scheduler.weights"]
$ENTRY
EOF
        fi

        if grep -qF "$ENTRY" "$PYPROJECT"; then
            echo ">>> [PLUGIN] OK: entry point aggiunto in pyproject.toml"
        else
            echo ">>> [PLUGIN][ERRORE] Impossibile aggiungere entry point a pyproject.toml"
            return 1
        fi
    fi

    echo ">>> [PLUGIN] Reinstallazione di cinder in editable mode"
    if (cd "$CINDER_DIR" && pip3 install -e .); then
        echo ">>> [PLUGIN] OK: cinder reinstallato"
    else
        echo ">>> [PLUGIN][ERRORE] pip3 install -e . fallito"
        return 1
    fi
}

function configure_cinder_compliance {
    echo ">>> [PLUGIN] FASE POST-CONFIG: aggiornamento cinder.conf"

    local CONF="/etc/cinder/cinder.conf"
    local WEIGHERS="PerformanceWeigher"

    echo ">>> [PLUGIN] CONF: ${CONF}"
    echo ">>> [PLUGIN] scheduler_default_weighers: ${WEIGHERS}"

    if [[ ! -f "$CONF" ]]; then
        echo ">>> [PLUGIN][ERRORE] File di configurazione non trovato: ${CONF}"
        return 1
    fi

    if iniset "$CONF" DEFAULT scheduler_default_weighers "$WEIGHERS"; then
        echo ">>> [PLUGIN] OK: scheduler_default_weighers aggiornato"
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