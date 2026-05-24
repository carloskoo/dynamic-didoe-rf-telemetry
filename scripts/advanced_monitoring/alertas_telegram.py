#!/usr/bin/env python3
import os
import pandas as pd
import requests

BASE="/home/carlos/epmp_monitor"
FILE=f"{BASE}/reportes/dataset_operador.csv"
STATE_FILE=f"{BASE}/logs/ultimo_estado_telegram.txt"

# CAMBIA ESTOS DOS VALORES
TOKEN="TU_TOKEN_TELEGRAM"
CHAT_ID="TU_CHAT_ID"

if not os.path.exists(FILE):
    print("No existe dataset_operador.csv")
    raise SystemExit(0)

df=pd.read_csv(FILE)
if df.empty:
    print("Dataset vacío")
    raise SystemExit(0)

ult=df.tail(1).iloc[0]

ts=ult.get("ts","")
estado=str(ult.get("estado_operador","SIN_ESTADO"))
prob=float(ult.get("prob_caida",0))*100
snr=ult.get("dl_snr_db","")
rssi=ult.get("dl_rssi_dbm","")
rate=ult.get("dl_rate","")

if prob < 30 and estado == "ESTABLE":
    print("Estado estable, no alerta")
    raise SystemExit(0)

estado_anterior=""
if os.path.exists(STATE_FILE):
    with open(STATE_FILE,"r") as f:
        estado_anterior=f.read().strip()

firma=f"{estado}-{int(prob//10)*10}"

if firma == estado_anterior:
    print("Alerta repetida, no se envía")
    raise SystemExit(0)

icono="⚠️"
if estado == "CRITICO" or prob >= 65:
    icono="🚨"

mensaje=f"""{icono} ALERTA NOC RF

Estado: {estado}
Probabilidad de caída: {prob:.1f}%

SNR: {snr} dB
RSSI: {rssi} dBm
Throughput: {rate} Mbps

Hora: {ts}
"""

url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"
r=requests.post(url, data={"chat_id": CHAT_ID, "text": mensaje}, timeout=10)

if r.status_code == 200:
    with open(STATE_FILE,"w") as f:
        f.write(firma)
    print("Alerta enviada:", firma)
else:
    print("Error Telegram:", r.text)
