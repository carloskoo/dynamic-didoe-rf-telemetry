#!/usr/bin/env bash
set -u

source /home/carlos/epmp_monitor/config/epmp.conf

PASSWORD="$(cat "$PASS_FILE")"

TODAY="$(date +%F)"
CSV_FILE="$DATA_DIR/agg_ap_${TODAY}.csv"
ERR_FILE="$LOG_DIR/agg_ap_${TODAY}.err.log"
RAW_FILE="$LOG_DIR/raw_show_sta_${TODAY}.log"

mkdir -p "$DATA_DIR" "$LOG_DIR"

if [[ ! -f "$CSV_FILE" ]]; then
    echo "ts,role,ip,peer_ip,dl_mcs,ul_mcs,dl_snr_db,ul_snr_db,dl_rssi_dbm,ul_rssi_dbm,dl_rate,note" > "$CSV_FILE"
fi

run_show_sta() {
    sshpass -p "$PASSWORD" ssh $SSH_OPTS "${RADIO_USER}@${AP_IP}" "show sta" 2>>"$ERR_FILE"
}

extract_first_value() {
    local text="$1"
    local key="$2"
    echo "$text" | awk -v k="$key" '
        index($0,k)>0 {
            for(i=1;i<=NF;i++){
                if($i==k && (i+1)<=NF){
                    print $(i+1)
                    exit
                }
            }
        }'
}

extract_after_colon() {
    local text="$1"
    local key="$2"
    echo "$text" | awk -F':' -v k="$key" '
        index($1,k)>0 {
            gsub(/^[ \t]+|[ \t]+$/, "", $2)
            print $2
            exit
        }'
}

normalize_value() {
    local v="${1:-}"
    v="$(echo "$v" | tr -d '\r' | xargs 2>/dev/null || true)"
    echo "$v"
}

sanitize_csv_field() {
    local v="${1:-}"
    v="$(echo "$v" | tr -d '\r\n' | tr ',' ';')"
    echo "$v"
}

while true; do
    TS="$(date --iso-8601=seconds)"
    TODAY_NOW="$(date +%F)"

    if [[ "$TODAY_NOW" != "$TODAY" ]]; then
        TODAY="$TODAY_NOW"
        CSV_FILE="$DATA_DIR/agg_ap_${TODAY}.csv"
        ERR_FILE="$LOG_DIR/agg_ap_${TODAY}.err.log"
        RAW_FILE="$LOG_DIR/raw_show_sta_${TODAY}.log"

        if [[ ! -f "$CSV_FILE" ]]; then
            echo "ts,role,ip,peer_ip,dl_mcs,ul_mcs,dl_snr_db,ul_snr_db,dl_rssi_dbm,ul_rssi_dbm,dl_rate,note" > "$CSV_FILE"
        fi
    fi

    RAW="$(run_show_sta || true)"

    echo "===== $TS =====" >> "$RAW_FILE"
    echo "$RAW" >> "$RAW_FILE"
    echo >> "$RAW_FILE"

    if [[ -z "$(echo "$RAW" | xargs 2>/dev/null || true)" ]]; then
        printf "%s,%s,%s,,,,,,,,,,%s\n" \
        "$TS" "AP" "$AP_IP" "empty_show_sta" >> "$CSV_FILE"
        sleep "$INTERVAL_SECONDS"
        continue
    fi

    # Intenta extraer por nombre exacto de campo típico en ePMP
    PEER_IP="$(extract_first_value "$RAW" "connectedSTAIP")"
    DL_MCS="$(extract_first_value "$RAW" "connectedSTADLMCS")"
    UL_MCS="$(extract_first_value "$RAW" "connectedSTAULMCS")"
    DL_SNR="$(extract_first_value "$RAW" "connectedSTADLSNR")"
    UL_SNR="$(extract_first_value "$RAW" "connectedSTAULSNR")"
    DL_RSSI="$(extract_first_value "$RAW" "connectedSTADLRSSI")"
    UL_RSSI="$(extract_first_value "$RAW" "connectedSTAULRSSI")"
    DL_RATE="$(extract_first_value "$RAW" "connectedSTADLRateMbps")"

    # Fallback por si el firmware usa ":" en vez de espacio
    [[ -z "$PEER_IP" ]] && PEER_IP="$(extract_after_colon "$RAW" "connectedSTAIP")"
    [[ -z "$DL_MCS"  ]] && DL_MCS="$(extract_after_colon "$RAW" "connectedSTADLMCS")"
    [[ -z "$UL_MCS"  ]] && UL_MCS="$(extract_after_colon "$RAW" "connectedSTAULMCS")"
    [[ -z "$DL_SNR"  ]] && DL_SNR="$(extract_after_colon "$RAW" "connectedSTADLSNR")"
    [[ -z "$UL_SNR"  ]] && UL_SNR="$(extract_after_colon "$RAW" "connectedSTAULSNR")"
    [[ -z "$DL_RSSI" ]] && DL_RSSI="$(extract_after_colon "$RAW" "connectedSTADLRSSI")"
    [[ -z "$UL_RSSI" ]] && UL_RSSI="$(extract_after_colon "$RAW" "connectedSTAULRSSI")"
    [[ -z "$DL_RATE" ]] && DL_RATE="$(extract_after_colon "$RAW" "connectedSTADLRateMbps")"

    PEER_IP="$(normalize_value "$PEER_IP")"
    DL_MCS="$(normalize_value "$DL_MCS")"
    UL_MCS="$(normalize_value "$UL_MCS")"
    DL_SNR="$(normalize_value "$DL_SNR")"
    UL_SNR="$(normalize_value "$UL_SNR")"
    DL_RSSI="$(normalize_value "$DL_RSSI")"
    UL_RSSI="$(normalize_value "$UL_RSSI")"
    DL_RATE="$(normalize_value "$DL_RATE")"

    NOTE="ok"

    if [[ -z "$PEER_IP" && -z "$DL_MCS" && -z "$UL_MCS" && -z "$DL_SNR" && -z "$UL_SNR" && -z "$DL_RSSI" && -z "$UL_RSSI" ]]; then
        NOTE="parse_failed_check_raw_log"
    fi

    PEER_IP="$(sanitize_csv_field "$PEER_IP")"
    DL_MCS="$(sanitize_csv_field "$DL_MCS")"
    UL_MCS="$(sanitize_csv_field "$UL_MCS")"
    DL_SNR="$(sanitize_csv_field "$DL_SNR")"
    UL_SNR="$(sanitize_csv_field "$UL_SNR")"
    DL_RSSI="$(sanitize_csv_field "$DL_RSSI")"
    UL_RSSI="$(sanitize_csv_field "$UL_RSSI")"
    DL_RATE="$(sanitize_csv_field "$DL_RATE")"
    NOTE="$(sanitize_csv_field "$NOTE")"

    printf "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" \
    "$TS" "AP" "$AP_IP" "$PEER_IP" "$DL_MCS" "$UL_MCS" \
    "$DL_SNR" "$UL_SNR" "$DL_RSSI" "$UL_RSSI" "$DL_RATE" "$NOTE" >> "$CSV_FILE"

    sleep "$INTERVAL_SECONDS"
done
