#!/usr/bin/env bash
set -u

source /home/carlos/epmp_monitor/config/epmp.conf

PID_FILE="$LOG_DIR/agg_ap.pid"
SCRIPT="$BIN_DIR/capture_agg_ap.sh"

mkdir -p "$LOG_DIR"

if pgrep -af "$SCRIPT" >/dev/null; then
    echo "Ya existe una captura agg en ejecución"
    pgrep -af "$SCRIPT"
    exit 1
fi

nohup bash "$SCRIPT" >/dev/null 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

echo "Captura agg iniciada con PID $PID"
