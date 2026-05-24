#!/usr/bin/env bash
set -e

INFILE="${1:-/home/carlos/epmp_logs/epmp_local_$(date +%F).csv}"
OUTFILE="${2:-/home/carlos/epmp_logs/ap_snr_only_$(date +%F).csv}"

awk -F',' '
BEGIN {
  OFS=","
  print "ts,ip,mcs_dl,mcs_ul,snr_dl,snr_ul,rssi_c0p,rssi_c0e,rssi_c1p,rssi_c1e,dl_rate,sta_dl_rssi,sta_ul_rssi"
}
NR>1 {
  line=$0
  gsub(/"/,"",line)
  split(line,a,",")
  if (a[2]=="AP") {
    print a[1],a[3],a[8],a[9],a[10],a[11],a[12],a[13],a[14],a[15],a[16],a[18],a[19]
  }
}
' "$INFILE" > "$OUTFILE"

echo "Archivo AP + métricas útiles generado en: $OUTFILE"
