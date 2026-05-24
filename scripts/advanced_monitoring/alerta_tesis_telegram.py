#!/usr/bin/env python3
import os
import time
import requests
import pandas as pd
from sqlalchemy import create_engine, text

BASE="/home/carlos/epmp_monitor"
LOG_DIR=f"{BASE}/logs"
STATE_FILE=f"{LOG_DIR}/estado_alerta_tesis.txt"

DB_URL="postgresql://carlos:1234@localhost:5432/epmp_noc"

TOKEN="<YOUR_TOKEN"
CHAT_ID="<YOUR_CHAT_ID>"

os.makedirs(LOG_DIR, exist_ok=True)

engine=create_engine(DB_URL)

SQL="""
SELECT
  ts,
  ip,
  peer_ip,
  dl_snr_db,
  dl_rssi_dbm,
  dl_rate,
  snr_diff,
  rssi_diff,
  rate_diff,
  snr_avg,
  rate_avg,
  snr_std,
  riesgo_nivel,
  evento,
  CASE
    WHEN snr_diff < -2 THEN 2
    WHEN snr_diff < -1 AND snr_avg < 20 THEN 1
    ELSE 0
  END AS degradacion_real
FROM metricas_predictivas
ORDER BY ts DESC
LIMIT 5;
"""

df=pd.read_sql(text(SQL), engine)

if df.empty:
    print("Sin datos para alerta")
    raise SystemExit(0)

df=df.sort_values("ts")

ultimo=df.iloc[-1]

degradacion=int(ultimo["degradacion_real"])
ts=str(ultimo["ts"])

if degradacion < 1:
    print("Estado normal, no se envía alerta")
    with open(STATE_FILE,"w") as f:
        f.write("NORMAL")
    raise SystemExit(0)

# Confirmación por ventana: al menos 1 evento en las últimas 5 muestras
eventos=int((df["degradacion_real"] >= 1).sum())

if eventos < 1:
    print("Evento no confirmado")
    raise SystemExit(0)

snr=round(float(ultimo["dl_snr_db"]),2) if pd.notna(ultimo["dl_snr_db"]) else "N/D"
rssi=round(float(ultimo["dl_rssi_dbm"]),2) if pd.notna(ultimo["dl_rssi_dbm"]) else "N/D"
rate=round(float(ultimo["dl_rate"]),2) if pd.notna(ultimo["dl_rate"]) else "N/D"
snr_diff=round(float(ultimo["snr_diff"]),2) if pd.notna(ultimo["snr_diff"]) else "N/D"
snr_avg=round(float(ultimo["snr_avg"]),2) if pd.notna(ultimo["snr_avg"]) else "N/D"
snr_std=round(float(ultimo["snr_std"]),2) if pd.notna(ultimo["snr_std"]) else "N/D"
rate_avg=round(float(ultimo["rate_avg"]),2) if pd.notna(ultimo["rate_avg"]) else "N/D"

ip=ultimo["ip"] if pd.notna(ultimo["ip"]) else "N/D"
peer_ip=ultimo["peer_ip"] if pd.notna(ultimo["peer_ip"]) else "N/D"
evento=ultimo["evento"] if pd.notna(ultimo["evento"]) else "N/D"
riesgo=ultimo["riesgo_nivel"] if pd.notna(ultimo["riesgo_nivel"]) else "N/D"

if degradacion == 2:
    severidad="CRÍTICA / PRE-CAÍDA"
    emoji="🚨"
else:
    severidad="ADVERTENCIA / DEGRADACIÓN TEMPRANA"
    emoji="⚠️"

firma=f"{degradacion}-{snr}-{snr_diff}-{ts[:16]}"

if os.path.exists(STATE_FILE):
    with open(STATE_FILE,"r") as f:
        anterior=f.read().strip()
    if anterior == firma:
        print("Alerta repetida, no enviada")
        raise SystemExit(0)

mensaje=f"""{emoji} ALERTA NOC RF - IA PREDICTIVA

Severidad: {severidad}
Estado IA: degradacion_real = {degradacion}

Hora: {ts}

📡 Enlace:
AP: {ip}
SM/Peer: {peer_ip}

📊 Métricas RF:
SNR actual: {snr} dB
SNR promedio: {snr_avg} dB
Variación SNR: {snr_diff} dB
Volatilidad SNR: {snr_std}

RSSI: {rssi} dBm
Throughput actual: {rate} Mbps
Throughput promedio: {rate_avg} Mbps

🧠 Diagnóstico:
Evento: {evento}
Riesgo: {riesgo}

📌 Interpretación:
El sistema detectó una degradación temprana del enlace antes de una posible caída.

✅ Acción recomendada:
Revisar interferencia, alineación, nivel RSSI, ruido RF y estabilidad del SM/AP.
"""

url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"

try:
    r=requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": mensaje
    }, timeout=10)

    if r.status_code == 200:
        with open(STATE_FILE,"w") as f:
            f.write(firma)
        print("Alerta tesis enviada:", severidad)
    else:
        print("Error Telegram:", r.text)

except Exception as e:
    print("Error enviando Telegram:", e)
