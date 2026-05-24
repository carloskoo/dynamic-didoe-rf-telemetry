#!/usr/bin/env bash
set -e

INFILE="${1:-/home/carlos/epmp_logs/epmp_local_$(date +%F).csv}"
OUTFILE="${2:-/home/carlos/epmp_logs/epmp_ap_only_$(date +%F).csv}"

awk -F',' '
NR==1 {print; next}
{
  line=$0
  gsub(/"/,"",line)
  split(line,a,",")
  if (a[2]=="AP") print line
}
' "$INFILE" > "$OUTFILE"

echo "Archivo AP-only generado en: $OUTFILE"
