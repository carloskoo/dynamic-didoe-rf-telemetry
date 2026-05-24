#!/usr/bin/env bash
set -e

BASE="/home/carlos/epmp_monitor"
PY="$BASE/venv/bin/python"
LOG="$BASE/logs/pipeline.log"

mkdir -p "$BASE/logs"

echo "===== PIPELINE $(date '+%F %T') =====" >> "$LOG"

CSV_COUNT=$(find "$BASE/data" -maxdepth 1 -type f -name "agg_ap_*.csv" | wc -l)
echo "CSV detectados: $CSV_COUNT" >> "$LOG"

if [ "$CSV_COUNT" -eq 0 ]; then
  echo "SIN CSV" >> "$LOG"
  echo "===== FIN =====" >> "$LOG"
  exit 0
fi

"$PY" "$BASE/bin/modelo_avanzado.py" >> "$BASE/logs/modelo.log" 2>&1
"$PY" "$BASE/bin/estado_predictivo.py" >> "$BASE/logs/predictivo.log" 2>&1
"$PY" "$BASE/bin/prediccion_temprana.py" >> "$BASE/logs/prediccion_temprana.log" 2>&1
PGPASSWORD=1234 "$PY" "$BASE/bin/ia_operador.py" >> "$BASE/logs/ia.log" 2>&1
PGPASSWORD=1234 "$PY" "$BASE/bin/db_refresh.py" >> "$BASE/logs/db.log" 2>&1
"$PY" "$BASE/bin/alerta_tesis_telegram.py" >> "$BASE/logs/alerta_tesis.log" 2>&1

echo "===== FIN =====" >> "$LOG"
