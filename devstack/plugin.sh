#!/bin/bash
set -x

echo ">>> [PLUGIN] fase: $1 / $2"

install_sysstat() {
    echo ">>> [PLUGIN] Installazione sysstat"

    if command -v iostat >/dev/null 2>&1; then
        echo ">>> [PLUGIN] iostat già installato"
    else
        sudo apt-get update
        sudo apt-get install -y sysstat || return 1
        echo ">>> [PLUGIN] sysstat installato correttamente"
    fi
}

install_storage_bonus_config() {
    local CONFIG_FILE="/etc/cinder/performance_storage_bonus.json"

    echo ">>> [PLUGIN] Creazione file configurazione bonus storage"
    echo ">>> [PLUGIN] CONFIG_FILE = $CONFIG_FILE"

    sudo tee "$CONFIG_FILE" >/dev/null <<EOF
[
  {
    "storage_type_plugin": "SSD",
    "storage_bonus": 10.0
  },
  {
    "storage_type_plugin": "HDD",
    "storage_bonus": 0.0
  }
]
EOF

    sudo chmod 644 "$CONFIG_FILE" || return 1

    echo ">>> [PLUGIN] File bonus storage creato correttamente"
}

uninstall_storage_bonus_config() {
    local CONFIG_FILE="/etc/cinder/performance_storage.json"

    echo ">>> [PLUGIN] Rimozione file configurazione bonus storage"

    if [[ -f "$CONFIG_FILE" ]]; then
        sudo rm -f "$CONFIG_FILE" || return 1
        echo ">>> [PLUGIN] File bonus storage rimosso"
    else
        echo ">>> [PLUGIN] File bonus storage non presente, niente da rimuovere"
    fi
}

uninstall_sysstat() {
    echo ">>> [PLUGIN] Disinstallazione sysstat"

    if dpkg -s sysstat >/dev/null 2>&1; then
        sudo apt-get remove -y sysstat || return 1
        sudo apt-get autoremove -y || return 1
        echo ">>> [PLUGIN] sysstat rimosso correttamente"
    else
        echo ">>> [PLUGIN] sysstat non installato, niente da rimuovere"
    fi
}

install_performance_collector() {
    local SRC_DIR="/opt/stack/performance-weighted-scheduler/devstack/modulo_1_performance_collector"
    local DST_DIR="/opt/stack/cinder/cinder/volume/performance_weighted_scheduler_module1"

    echo ">>> [PLUGIN] Installazione Modulo 1 - Performance Collector"
    echo ">>> [PLUGIN] SRC_DIR = $SRC_DIR"
    echo ">>> [PLUGIN] DST_DIR = $DST_DIR"

    [[ -d "$SRC_DIR" ]] || { echo ">>> [PLUGIN][ERRORE] Directory sorgente non trovata: $SRC_DIR"; return 1; }

    mkdir -p "$DST_DIR" || return 1
    touch "$DST_DIR/__init__.py" || return 1

    cp "${SRC_DIR}"/*.py "$DST_DIR"/ || return 1

    echo ">>> [PLUGIN] Modulo 1 copiato correttamente"
}

uninstall_performance_collector() {
    local DST_DIR="/opt/stack/cinder/cinder/volume/performance_weighted_scheduler_module1"

    echo ">>> [PLUGIN] Disinstallazione Modulo 1 - Performance Collector"
    echo ">>> [PLUGIN] DST_DIR = $DST_DIR"

    if [[ -d "$DST_DIR" ]]; then
        rm -rf "$DST_DIR" || return 1
        echo ">>> [PLUGIN] Modulo 1 rimosso correttamente"
    else
        echo ">>> [PLUGIN] Cartella Modulo 1 non presente, niente da rimuovere"
    fi
}

install_weigher_extension() {
    local SRC_DIR="/opt/stack/performance-weighted-scheduler/devstack/modulo_2_weigher_extension"
    local WEIGHTS_DIR="/opt/stack/cinder/cinder/scheduler/weights"
    local MODULE2_DIR="/opt/stack/cinder/cinder/scheduler/performance_weighted_scheduler_module2"
    local CINDER_DIR="/opt/stack/cinder"
    local PYPROJECT="${CINDER_DIR}/pyproject.toml"
    local ENTRY='PerformanceWeigher = "cinder.scheduler.weights.performance_weigher:PerformanceWeigher"'

    echo ">>> [PLUGIN] Installazione Modulo 2 - Weigher Extension"
    echo ">>> [PLUGIN] SRC_DIR = $SRC_DIR"
    echo ">>> [PLUGIN] WEIGHTS_DIR = $WEIGHTS_DIR"
    echo ">>> [PLUGIN] MODULE2_DIR = $MODULE2_DIR"

    [[ -d "$SRC_DIR" ]] || { echo ">>> [PLUGIN][ERRORE] Directory sorgente non trovata: $SRC_DIR"; return 1; }
    [[ -d "$WEIGHTS_DIR" ]] || { echo ">>> [PLUGIN][ERRORE] Directory target weights non trovata: $WEIGHTS_DIR"; return 1; }
    [[ -f "$PYPROJECT" ]] || { echo ">>> [PLUGIN][ERRORE] pyproject.toml non trovato: $PYPROJECT"; return 1; }

    mkdir -p "$MODULE2_DIR" || return 1
    touch "$MODULE2_DIR/__init__.py" || return 1

    echo ">>> [PLUGIN] Copia performance_weigher.py in scheduler/weights"
    cp "${SRC_DIR}/performance_weigher.py" "${WEIGHTS_DIR}/performance_weigher.py" || return 1

    echo ">>> [PLUGIN] Copia file di supporto del Modulo 2 nella cartella dedicata"
    find "$SRC_DIR" -maxdepth 1 -type f -name "*.py" ! -name "performance_weigher.py" -exec cp {} "$MODULE2_DIR"/ \; || return 1

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
    iniset "$CONF" DEFAULT performance_collector_interval 30 || return 1

    echo ">>> [PLUGIN] debug = True"
    echo ">>> [PLUGIN] performance_collector_interval = 30"
}

configure_weigher_extension() {
    local CONF="/etc/cinder/cinder.conf"
    local CURRENT
    local UPDATED

    echo ">>> [PLUGIN] Configurazione Modulo 2 - Weigher Extension"
    echo ">>> [PLUGIN] CONF = $CONF"

    [[ -f "$CONF" ]] || { echo ">>> [PLUGIN][ERRORE] File di configurazione non trovato: $CONF"; return 1; }

    CURRENT=$(iniget "$CONF" DEFAULT scheduler_default_weighers)

	echo ">>> [PLUGIN] CURRENT scheduler_default_weighers = $CURRENT"
	
    if [[ -z "$CURRENT" ]]; then
        UPDATED="PerformanceWeigher"
    elif [[ "$CURRENT" == *"PerformanceWeigher"* ]]; then
        UPDATED="$CURRENT"
    else
        UPDATED="${CURRENT},PerformanceWeigher"
    fi

    iniset "$CONF" DEFAULT scheduler_default_weighers "$UPDATED" || return 1

    echo ">>> [PLUGIN] scheduler_default_weighers = $UPDATED"
}

start_performance_collector_daemon() {
    local CINDER_DIR="/opt/stack/cinder"
    local MODULE1_PKG="cinder.volume.performance_weighted_scheduler_module1.collector_daemon"
    local LOG_FILE="/tmp/performance_weighted_scheduler_collector.log"
    local PID_FILE="/tmp/performance_weighted_scheduler_collector.pid"

    echo ">>> [PLUGIN] Avvio collector periodico"
    echo ">>> [PLUGIN] CINDER_DIR = $CINDER_DIR"
    echo ">>> [PLUGIN] MODULE1_PKG = $MODULE1_PKG"

    if [[ -f "$PID_FILE" ]] && ps -p "$(cat "$PID_FILE")" >/dev/null 2>&1; then
        echo ">>> [PLUGIN] Collector già in esecuzione con PID $(cat "$PID_FILE")"
        return 0
    fi

    cd "$CINDER_DIR" || return 1

    nohup python3 -m "$MODULE1_PKG" >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"

    echo ">>> [PLUGIN] Collector periodico avviato con PID $(cat "$PID_FILE")"
    echo ">>> [PLUGIN] Log collector: $LOG_FILE"
}

stop_performance_collector_daemon() {
    local PID_FILE="/tmp/performance_weighted_scheduler_collector.pid"

    echo ">>> [PLUGIN] Arresto collector periodico"

    if [[ -f "$PID_FILE" ]]; then
        kill "$(cat "$PID_FILE")" || true
        rm -f "$PID_FILE"
        echo ">>> [PLUGIN] Collector periodico arrestato"
    else
        echo ">>> [PLUGIN] Nessun PID file trovato, niente da arrestare"
    fi
}

uninstall_weigher_extension() {
    local MODULE2_DIR="/opt/stack/cinder/cinder/scheduler/performance_weighted_scheduler_module2"
    local WEIGHER_FILE="/opt/stack/cinder/cinder/scheduler/weights/performance_weigher.py"
    local PYPROJECT="/opt/stack/cinder/pyproject.toml"
    local CONF="/etc/cinder/cinder.conf"

    echo ">>> [PLUGIN] Disinstallazione Modulo 2 - Weigher Extension"

    if [[ -d "$MODULE2_DIR" ]]; then
        rm -rf "$MODULE2_DIR" || return 1
        echo ">>> [PLUGIN] Cartella Modulo 2 rimossa correttamente"
    else
        echo ">>> [PLUGIN] Cartella Modulo 2 non presente"
    fi

    if [[ -f "$WEIGHER_FILE" ]]; then
        rm -f "$WEIGHER_FILE" || return 1
        echo ">>> [PLUGIN] File performance_weigher.py rimosso"
    else
        echo ">>> [PLUGIN] performance_weigher.py non presente"
    fi

    if [[ -f "$PYPROJECT" ]]; then
        sed -i '/PerformanceWeigher = "cinder.scheduler.weights.performance_weigher:PerformanceWeigher"/d' "$PYPROJECT" || return 1
        echo ">>> [PLUGIN] Riferimento a PerformanceWeigher rimosso da pyproject.toml"
    else
        echo ">>> [PLUGIN] pyproject.toml non trovato, nessuna modifica eseguita"
    fi

    if [[ -f "$CONF" ]]; then
        local CURRENT
        local UPDATED

        CURRENT=$(iniget "$CONF" DEFAULT scheduler_default_weighers)

        if [[ -n "$CURRENT" ]]; then
            UPDATED=$(echo "$CURRENT" | sed 's/\(^\|,\)PerformanceWeigher\(,\|$\)/\1/g' | sed 's/,,*/,/g' | sed 's/^,\|,$//g')
            iniset "$CONF" DEFAULT scheduler_default_weighers "$UPDATED" || return 1
            echo ">>> [PLUGIN] scheduler_default_weighers aggiornato a: $UPDATED"
        fi
    fi
}

if [[ "$1" == "stack" && "$2" == "install" ]]; then
    install_sysstat || exit 1
    install_performance_collector || exit 1
    install_weigher_extension || exit 1
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_performance_collector || exit 1
    configure_weigher_extension || exit 1
    start_performance_collector_daemon || exit 1
	install_storage_bonus_config || exit 1
elif [[ "$1" == "unstack" ]]; then
    stop_performance_collector_daemon || exit 1
    uninstall_performance_collector || exit 1
    uninstall_weigher_extension || exit 1
	uninstall_storage_bonus_config || exit 1
    uninstall_sysstat || exit 1
fi