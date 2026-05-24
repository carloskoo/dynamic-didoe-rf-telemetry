#!/usr/bin/env bash
FILE="/home/carlos/epmp_logs/epmp_local_$(date +%F).csv"
REJ="/home/carlos/epmp_logs/epmp_reject_$(date +%F).csv"

echo "=== PROCESO ==="
ps aux | grep poll_epmp.sh | grep -v grep || echo "No está corriendo"

echo
echo "=== CSV DEL DÍA ==="
ls -lh "$FILE" 2>/dev/null || echo "No existe"

echo
echo "=== ÚLTIMAS 6 FILAS ==="
tail -n 6 "$FILE" 2>/dev/null || echo "Sin datos"

echo
echo "=== REJECT DEL DÍA ==="
ls -lh "$REJ" 2>/dev/null || echo "No existe"

echo
echo "=== ÚLTIMOS REJECTS ==="
tail -n 10 "$REJ" 2>/dev/null || echo "Sin rejects"
