#!/bin/bash

set -e

BASE_DIR="/opt/stack/data"
DEVSTACK_DIR="$HOME/devstack"

sudo mkdir -p "$BASE_DIR"
sudo chown "$USER:$USER" "$BASE_DIR"

create_vg() {
    local size=$1
    local file=$2
    local vg_name=$3

    echo "Creazione file $file (${size})..."
    sudo truncate -s "$size" "$BASE_DIR/$file"

    echo "Associazione loop device..."
    LOOP_DEV=$(sudo losetup -f --show "$BASE_DIR/$file")

    echo "Creazione volume group $vg_name su $LOOP_DEV..."
    sudo vgcreate "$vg_name" "$LOOP_DEV"

    echo "Completato: $vg_name"
    echo "-----------------------------"
}

create_vg "5G" "vg-low-backing-file" "vg-low"
create_vg "20G" "vg-mid-backing-file" "vg-mid"
create_vg "100G" "vg-high-backing-file" "vg-high"

echo "Tutti i volume group sono stati creati con successo."

echo "Caricamento credenziali OpenStack..."
cd "$DEVSTACK_DIR"
source openrc admin admin

echo "Creazione volume type general_storage..."
openstack volume type create general_storage || echo "Volume type general_storage già esistente"

echo "Restart servizio cinder-volume..."
sudo systemctl restart devstack@c-vol

echo "Restart servizio cinder-scheduler..."
sudo systemctl restart devstack@c-sch

echo "Restart servizio cinder-api..."
sudo systemctl restart devstack@c-api

echo "Installazione oslo.rootwrap nel virtual environment DevStack..."
/opt/stack/data/venv/bin/pip install --ignore-installed --no-user oslo.rootwrap

echo "Setup completato."