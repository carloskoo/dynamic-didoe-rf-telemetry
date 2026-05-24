#!/usr/bin/env bash
set -e

INFILE="${1:-/home/carlos/epmp_logs/epmp_local_$(date +%F).csv}"
OUTFILE="${2:-/home/carlos/epmp_logs/epmp_clean_$(date +%F).csv}"

awk -F',' '
BEGIN {
  OFS=","
  print "ts,role,ip,mcs_dl,mcs_ul,snr_dl,snr_ul,rssi_c0p,rssi_c0e,rssi_c1p,rssi_c1e,dl_rate,sta_dl_rssi,sta_ul_rssi"
}
NR>1 {
  gsub(/^"/,"",$1)
  gsub(/"$/,"",$NF)
  gsub(/"/,"",$0)
  print $1,$2,$3,$8,$9,$10,$11,$12,$13,$14,$15,$16,$18,$19
}
' "$INFILE" > "$OUTFILE"

echo "CSV limpio generado en: $OUTFILE"
