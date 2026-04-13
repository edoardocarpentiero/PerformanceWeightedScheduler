#!/bin/bash

function install_cinder_compliance {
    echo ">>> [PLUGIN] FASE INSTALL: Copia del file PerformanceWeigher"
    
    SOURCE="/opt/stack/cinder-compliance/files/performance_weigher.py"
    TARGET_DIR="/opt/stack/cinder/cinder/scheduler/weights"

    if [ -f "$SOURCE" ]; then
        cp "$SOURCE" "$TARGET_DIR/"
        echo ">>> [PLUGIN] OK: File copiato in $TARGET_DIR"
    else
        echo ">>> [PLUGIN] ERRORE: Sorgente $SOURCE non trovata!"
    fi
}

function configure_cinder_compliance {
    echo ">>> [PLUGIN] FASE POST-CONFIG: Modifica cinder.conf"
    
    CONF="/etc/cinder/cinder.conf"

    if [ -f "$CONF" ]; then
        iniset $CONF DEFAULT scheduler_weight_classes "cinder.scheduler.weights.capacity.CapacityWeigher,cinder.scheduler.weights.performance_weigher.PerformanceWeigher"
        echo ">>> [PLUGIN] OK: scheduler_weight_classes aggiornato"
    else
        echo ">>> [PLUGIN] ERRORE: $CONF non trovato"
    fi
}

# Verifica se il plugin è attivo nel local.conf

if [[ "$1" == "stack" && "$2" == "install" ]]; then
	install_cinder_compliance
elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_cinder_compliance
fi
