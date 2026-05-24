#!/usr/bin/env python3
import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

BASE="/home/carlos/epmp_monitor"
IN=f"{BASE}/reportes/dataset_avanzado.csv"
OUT=f"{BASE}/reportes/dataset_operador.csv"
DB_URL="postgresql://carlos:1234@localhost:5432/epmp_noc"

if not os.path.exists(IN):
    print("No existe dataset_avanzado.csv")
    raise SystemExit(0)

df=pd.read_csv(IN)
df["ts"]=pd.to_datetime(df["ts"], errors="coerce")
df=df.dropna(subset=["ts"]).sort_values("ts").reset_index(drop=True)

for c in ["dl_snr_db","dl_rssi_dbm","dl_rate","snr_diff","rssi_diff","rate_diff","snr_avg","rate_avg","snr_std","riesgo"]:
    if c in df.columns:
        df[c]=pd.to_numeric(df[c], errors="coerce")
    else:
        df[c]=np.nan

df["snr_trend_5"]=df["dl_snr_db"].diff(5)
df["rate_trend_5"]=df["dl_rate"].diff(5)
df["rssi_trend_5"]=df["dl_rssi_dbm"].diff(5)

def clamp(x):
    return max(0, min(100, x))

def probabilidad(row):
    p=0

    # SNR
    if pd.notna(row["dl_snr_db"]):
        if row["dl_snr_db"] < 10:
            p += 45
        elif row["dl_snr_db"] < 15:
            p += 30
        elif row["dl_snr_db"] < 18:
            p += 15

    # RSSI
    if pd.notna(row["dl_rssi_dbm"]):
        if row["dl_rssi_dbm"] < -85:
            p += 25
        elif row["dl_rssi_dbm"] < -80:
            p += 15
        elif row["dl_rssi_dbm"] < -75:
            p += 8

    # Throughput
    if pd.notna(row["dl_rate"]):
        if row["dl_rate"] < 10:
            p += 35
        elif row["dl_rate"] < 30:
            p += 20
        elif row["dl_rate"] < 60:
            p += 10

    # Tendencias
    if pd.notna(row["snr_trend_5"]):
        if row["snr_trend_5"] < -5:
            p += 25
        elif row["snr_trend_5"] < -3:
            p += 15
        elif row["snr_trend_5"] < -1:
            p += 5

    if pd.notna(row["rate_trend_5"]):
        if row["rate_trend_5"] < -50:
            p += 25
        elif row["rate_trend_5"] < -25:
            p += 15
        elif row["rate_trend_5"] < -10:
            p += 5

    # Inestabilidad
    if pd.notna(row["snr_std"]):
        if row["snr_std"] > 5:
            p += 20
        elif row["snr_std"] > 3:
            p += 10

    return clamp(p)

df["prob_caida_raw"]=df.apply(probabilidad, axis=1) / 100.0

# Suavizado para que no sea 0/100 brusco
df["prob_caida"]=df["prob_caida_raw"].rolling(5, min_periods=1).mean()

df["estado_operador"]=pd.cut(
    df["prob_caida"],
    bins=[-0.01,0.30,0.65,1.01],
    labels=["ESTABLE","RIESGO","CRITICO"]
)

df.to_csv(OUT,index=False)

engine=create_engine(DB_URL)
df.to_sql("metricas_operador", engine, if_exists="replace", index=False)

print("IA OPERADOR SUAVIZADA OK:", OUT)
print(df[["ts","dl_snr_db","dl_rssi_dbm","dl_rate","prob_caida","estado_operador"]].tail(10))
