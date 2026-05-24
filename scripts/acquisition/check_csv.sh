#!/usr/bin/env bash

FILE="$1"

if [[ -z "$FILE" ]]; then
    echo "Uso: $0 archivo.csv"
    exit 1
fi

if [[ ! -f "$FILE" ]]; then
    echo "❌ Archivo no encontrado: $FILE"
    exit 1
fi

echo "======================================"
echo "VALIDANDO ARCHIVO: $FILE"
echo "======================================"

HEADER=$(head -n 1 "$FILE")
EXPECTED="ts,role,ip,peer_ip,dl_mcs,ul_mcs,dl_snr_db,ul_snr_db,dl_rssi_dbm,ul_rssi_dbm,dl_rate,note"

echo "Cabecera detectada:"
echo "$HEADER"
echo

if [[ "$HEADER" == "$EXPECTED" ]]; then
    echo "✔ Cabecera correcta"
else
    echo "⚠ Cabecera distinta a la esperada"
fi

echo
TOTAL=$(wc -l < "$FILE")
echo "Total de líneas: $TOTAL"

if [[ "$TOTAL" -le 1 ]]; then
    echo "❌ Archivo vacío o sin datos"
    exit 1
fi

echo
BAD_LINES=$(awk -F',' 'NF!=12 {print NR ":" $0}' "$FILE")
if [[ -n "$BAD_LINES" ]]; then
    echo "⚠ Líneas con número incorrecto de columnas:"
    echo "$BAD_LINES"
else
    echo "✔ Todas las filas tienen 12 columnas"
fi

echo
EMPTY_FIELDS=$(awk -F',' '
NR>1 {
    if($1=="" || $5=="" || $7=="" || $9=="" || $11=="")
        print NR ":" $0
}' "$FILE")
if [[ -n "$EMPTY_FIELDS" ]]; then
    echo "⚠ Registros con campos críticos vacíos:"
    echo "$EMPTY_FIELDS"
else
    echo "✔ No se detectaron campos críticos vacíos"
fi

echo
BAD_TS=$(awk -F',' '
NR>1 {
    if($1 !~ /^[0-9]{4}-[0-9]{2}-[0-9]{2}T/)
        print NR ":" $0
}' "$FILE")
if [[ -n "$BAD_TS" ]]; then
    echo "⚠ Registros con timestamp inválido:"
    echo "$BAD_TS"
else
    echo "✔ Formato de timestamp válido"
fi

echo
echo "======================================"
echo "RESULTADO FINAL"
echo "======================================"

if [[ -z "$BAD_LINES" && -z "$EMPTY_FIELDS" && -z "$BAD_TS" ]]; then
    echo "✔ ARCHIVO VÁLIDO PARA PROCESAMIENTO"
else
    echo "⚠ ARCHIVO CON OBSERVACIONES"
fi

echo "======================================"
