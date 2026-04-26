#!/bin/bash

set -e

VG_NAME="$1"
LV_NAME="test_io_lv"
LV_SIZE="512M"
WRITE_MB=200
READ_MB=200

if [[ -z "$VG_NAME" ]]; then
    echo "Uso: $0 <volume_group>"
    exit 1
fi

LV_PATH="/dev/${VG_NAME}/${LV_NAME}"

echo "[INFO] Creazione volume temporaneo ${LV_PATH} nel VG ${VG_NAME}..."
sudo lvcreate -L "${LV_SIZE}" -n "${LV_NAME}" "${VG_NAME}"

cleanup() {
    echo "[INFO] Rimozione volume temporaneo ${LV_PATH}..."
    sudo lvremove -f "${LV_PATH}" || true
}
trap cleanup EXIT

echo "[INFO] Avvio simulazione di scrittura su ${LV_PATH}..."
sudo dd if=/dev/zero of="${LV_PATH}" bs=1M count="${WRITE_MB}" oflag=direct status=progress

echo "[INFO] Scrittura completata"

echo "[INFO] Avvio simulazione di lettura da ${LV_PATH}..."
sudo dd if="${LV_PATH}" of=/dev/null bs=1M count="${READ_MB}" iflag=direct status=progress

echo "[INFO] Lettura completata"
echo "[INFO] Simulazione terminata con successo"