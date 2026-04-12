#!/bin/bash

echo ">>> CINDER-COMPLIANCE plugin.sh caricato"

function install_cinder_compliance {
    echo ">>> [PLUGIN] INSTALL phase"
}

function configure_cinder_compliance {
    echo ">>> [PLUGIN] CONFIGURE phase"
}

function init_cinder_compliance {
    echo ">>> [PLUGIN] INIT phase"
}

function start_cinder_compliance {
    echo ">>> [PLUGIN] START phase"
}

# 🔥 HOOK DevStack
if [[ "$1" == "stack" && "$2" == "install" ]]; then
    install_cinder_compliance
fi

if [[ "$1" == "stack" && "$2" == "post-config" ]]; then
    configure_cinder_compliance
fi

if [[ "$1" == "stack" && "$2" == "extra" ]]; then
    start_cinder_compliance
fi