#!/bin/bash


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
    (cd "$CINDER_DIR" && /opt/stack/data/venv/bin/python -m pip install -e .) || return 1

    echo ">>> [PLUGIN] Modulo 2 installato correttamente"
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
