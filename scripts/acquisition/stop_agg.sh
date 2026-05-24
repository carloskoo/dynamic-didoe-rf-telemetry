#!/usr/bin/env bash
set -u

source /home/carlos/epmp_monitor/config/epmp.conf

PID_FILE="$LOG_DIR/agg_ap.pid"
SCRIPT="$BIN_DIR/capture_agg_ap.sh"

if [[ -f "$PID_FILE" ]]; then
    PID="$(cat "$PID_FILE")"
    if kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$PID_FILE"
fi

pkill -f "$SCRIPT" 2>/dev/null || true

echo "Captura agg detenida"
