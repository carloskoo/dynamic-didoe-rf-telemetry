#!/usr/bin/env bash
set -u

LOG_DIR="/home/carlos/epmp_logs"

AP_IP="w.x.y.z1"
SM_IP="w.x.y.z2"
SSH_USER="admin"

AP_PASSFILE="${LOG_DIR}/.ap_pass"

CSV_FILE="${LOG_DIR}/epmp_local_$(date +%F).csv"
REJECT_FILE="${LOG_DIR}/epmp_reject_$(date +%F).csv"
DEBUG_FILE="${LOG_DIR}/epmp_debug_$(date +%F).log"
LOCK_FILE="${LOG_DIR}/.poll_epmp.lock"

ts_now() { date '+%FT%T%:z'; }

ssh_ap() {
  local cmd="$1"
  local opts=(-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=5)
  sshpass -f "$AP_PASSFILE" ssh "${opts[@]}" "${SSH_USER}@${AP_IP}" "$cmd"
}

emit_24() {
  local -n f="$1"
  local out="${f[1]}"
  for i in $(seq 2 24); do
    out+=",""${f[$i]}"
  done
  echo "$out"
}

mkdir -p "$LOG_DIR"

if [[ ! -f "$CSV_FILE" ]]; then
  echo "ts,role,ip,f4,f5,f6,f7,mcs_dl,mcs_ul,snr_dl,snr_ul,rssi_c0p,rssi_c0e,rssi_c1p,rssi_c1e,dl_rate,ul_rate,sta_dl_rssi,sta_ul_rssi,res20,res21,res22,res23,res24" > "$CSV_FILE"
fi

if [[ ! -f "$REJECT_FILE" ]]; then
  echo "ts,role,ip,reason,raw_line" > "$REJECT_FILE"
fi

touch "$DEBUG_FILE"

get_rssi_chains_ap() {
  local out
  out="$(ssh_ap "show rssi" 2>>"$DEBUG_FILE")" || return 1

  {
    echo "----- $(ts_now) show rssi raw -----"
    echo "$out"
    echo "-----------------------------------"
  } >> "$DEBUG_FILE"

  awk -F: '
    /chain 0 RSSI primary/   {gsub(/^[ \t]+|[ \t]+$/, "", $2); c0p=$2}
    /chain 0 RSSI extension/ {gsub(/^[ \t]+|[ \t]+$/, "", $2); c0e=$2}
    /chain 1 RSSI primary/   {gsub(/^[ \t]+|[ \t]+$/, "", $2); c1p=$2}
    /chain 1 RSSI extension/ {gsub(/^[ \t]+|[ \t]+$/, "", $2); c1e=$2}
    END {
      print (c0p ? c0p : "") "," \
            (c0e ? c0e : "") "," \
            (c1p ? c1p : "") "," \
            (c1e ? c1e : "")
    }
  ' <<<"$out"
}

get_sta_metrics() {
  local out
  out="$(ssh_ap "show sta" 2>>"$DEBUG_FILE")" || return 1

  {
    echo "----- $(ts_now) show sta raw -----"
    echo "$out"
    echo "----------------------------------"
  } >> "$DEBUG_FILE"

  awk -v sm="$SM_IP" '
    $1=="connectedSTAIP"         {ip=$2}
    $1=="connectedSTADLMCS"      {dlmcs=$2}
    $1=="connectedSTAULMCS"      {ulmcs=$2}
    $1=="connectedSTADLSNR"      {dlsnr=$2}
    $1=="connectedSTAULSNR"      {ulsnr=$2}
    $1=="connectedSTADLRateMbps" {dlrate=$2}
    $1=="connectedSTADLRSSI"     {dlrssi=$2}
    $1=="connectedSTAULRSSI"     {ulrssi=$2}
    (ip==sm && dlmcs!="" && ulmcs!="" && dlsnr!="" && ulsnr!="" && dlrssi!="" && ulrssi!="") {
      print dlmcs "," ulmcs "," dlsnr "," ulsnr "," dlrate "," dlrssi "," ulrssi
      exit
    }
  ' <<<"$out"
}

exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

TS="$(ts_now)"

declare -a AP SM
for i in $(seq 1 24); do
  AP[$i]=""
  SM[$i]=""
done

AP[1]="$TS"; AP[2]="AP"; AP[3]="$AP_IP"
SM[1]="$TS"; SM[2]="SM"; SM[3]="$SM_IP"

AP[4]="0"; AP[5]="137"; AP[6]="2"; AP[7]="2"
SM[4]="2"; SM[5]="2"; SM[6]="";  SM[7]=""

if rssi_line="$(get_rssi_chains_ap)"; then
  echo "$(ts_now) rssi_line=$rssi_line" >> "$DEBUG_FILE"
  IFS=, read -r c0p c0e c1p c1e <<<"$rssi_line"
  AP[12]="$c0p"; AP[13]="$c0e"; AP[14]="$c1p"; AP[15]="$c1e"
  SM[12]="$c0p"; SM[13]="$c0e"; SM[14]="$c1p"; SM[15]="$c1e"
else
  echo "\"$TS\",AP,$AP_IP,show_rssi_failed,\"\"" >> "$REJECT_FILE"
fi

if sta_line="$(get_sta_metrics)"; then
  echo "$(ts_now) sta_line=$sta_line" >> "$DEBUG_FILE"
  IFS=, read -r dlmcs ulmcs dlsnr ulsnr dlrate dlrssi ulrssi <<<"$sta_line"
  AP[8]="$dlmcs";  AP[9]="$ulmcs";  AP[10]="$dlsnr"; AP[11]="$ulsnr"
  SM[8]="$dlmcs";  SM[9]="$ulmcs";  SM[10]="$dlsnr"; SM[11]="$ulsnr"
  AP[16]="$dlrate"; SM[16]="$dlrate"
  AP[18]="$dlrssi"; AP[19]="$ulrssi"
  SM[18]="$dlrssi"; SM[19]="$ulrssi"
else
  echo "\"$TS\",AP,$AP_IP,show_sta_failed,\"\"" >> "$REJECT_FILE"
fi

emit_24 AP >> "$CSV_FILE"
emit_24 SM >> "$CSV_FILE"
