#!/bin/bash

set -e

VG_NAME="$1"
LV_NAME="test_io_lv"
LV_SIZE="512M"
WRITE_MB=200
READ_MB=200
SLEEP_SECONDS=1

if [[ -z "$VG_NAME" ]]; then
    echo "Uso: $0 <volume_group>"
    echo "Esempio: $0 vg-mid"
    exit 1
fi

LV_PATH="/dev/${VG_NAME}/${LV_NAME}"

cleanup() {
    echo ""
    echo "[INFO] Arresto simulatore I/O..."
    echo "[INFO] Rimozione volume temporaneo ${LV_PATH}..."
    sudo lvremove -f "${LV_PATH}" || true
    echo "[INFO] Simulatore terminato."
}

trap cleanup EXIT INT TERM

if sudo lvs "${VG_NAME}/${LV_NAME}" >/dev/null 2>&1; then
    echo "[WARN] Il volume temporaneo ${LV_PATH} esiste già. Lo rimuovo..."
    sudo lvremove -f "${LV_PATH}"
fi

echo "[INFO] Creazione volume temporaneo ${LV_PATH} nel VG ${VG_NAME}..."
sudo lvcreate -L "${LV_SIZE}" -n "${LV_NAME}" "${VG_NAME}"

echo "[INFO] Simulatore I/O avviato. Premi CTRL+C per fermarlo."

while true; do
    echo "[INFO] Scrittura su ${LV_PATH}..."
    sudo dd if=/dev/zero of="${LV_PATH}" bs=1M count="${WRITE_MB}" oflag=direct conv=fsync status=none

    echo "[INFO] Lettura da ${LV_PATH}..."
    sudo dd if="${LV_PATH}" of=/dev/null bs=1M count="${READ_MB}" iflag=direct status=none

    sleep "${SLEEP_SECONDS}"
done