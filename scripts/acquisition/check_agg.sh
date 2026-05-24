#!/usr/bin/env bash

source /home/carlos/epmp_monitor/config/epmp.conf

TODAY="$(date +%F)"
CSV_FILE="$DATA_DIR/agg_ap_${TODAY}.csv"
RAW_FILE="$LOG_DIR/raw_show_sta_${TODAY}.log"
PID_FILE="$LOG_DIR/agg_ap.pid"

EXPECTED_HEADER="ts,role,ip,peer_ip,dl_mcs,ul_mcs,dl_snr_db,ul_snr_db,dl_rssi_dbm,ul_rssi_dbm,dl_rate,note"

echo "======================================"
echo "REVISIÓN OPERATIVA DEL SISTEMA ePMP"
echo "Fecha: $(date)"
echo "======================================"
echo

# =========================
# 1. ESTADO DEL PROCESO
# =========================
echo "=== PROCESO ==="

if [[ -f "$PID_FILE" ]]; then
    PID="$(cat "$PID_FILE")"
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✔ Proceso activo con PID: $PID"
    else
        echo "⚠ Existe PID file, pero el proceso no está activo: $PID"
    fi
else
    echo "⚠ No existe PID file"
fi

echo

# =========================
# 2. ARCHIVO CSV DEL DÍA
# =========================
echo "=== CSV DEL DÍA ==="

if [[ -f "$CSV_FILE" ]]; then
    ls -lh "$CSV_FILE"
    echo

    HEADER="$(head -n 1 "$CSV_FILE")"
    if [[ "$HEADER" == "$EXPECTED_HEADER" ]]; then
        echo "✔ Cabecera correcta"
    else
        echo "⚠ Cabecera distinta a la esperada"
        echo "Cabecera detectada:"
        echo "$HEADER"
    fi

    TOTAL_LINES=$(wc -l < "$CSV_FILE")
    echo "Total de líneas: $TOTAL_LINES"
    echo

    echo "=== ÚLTIMAS 10 FILAS ==="
    tail -n 10 "$CSV_FILE"
else
    echo "❌ No existe el archivo CSV del día: $CSV_FILE"
fi

echo
# =========================
# 3. ARCHIVO RAW SHOW STA
# =========================
echo "=== RAW SHOW STA ==="

if [[ -f "$RAW_FILE" ]]; then
    ls -lh "$RAW_FILE"
    echo
    echo "=== ÚLTIMAS 30 LÍNEAS RAW ==="
    tail -n 30 "$RAW_FILE"
else
    echo "⚠ No existe el archivo RAW del día: $RAW_FILE"
fi

echo
echo "======================================"
echo "FIN DE LA REVISIÓN"
echo "======================================"
