#!/usr/bin/env python3

import pandas as pd
from sqlalchemy import create_engine
import os

BASE = "/home/carlos/epmp_monitor"
FILE = f"{BASE}/reportes/dataset_avanzado.csv"

DB_URL = "postgresql://carlos:1234@localhost:5432/epmp_noc"

if not os.path.exists(FILE):
    print("No existe dataset_avanzado.csv")
    exit()

df = pd.read_csv(FILE)

# --- NORMALIZAR ---
df["ts"] = pd.to_datetime(df["ts"])

# 🔴 MAPEO INTELIGENTE (POR SI CAMBIA EL NOMBRE)
if "rssi" not in df.columns:
    if "dl_rssi" in df.columns:
        df["rssi"] = df["dl_rssi"]
    elif "ul_rssi" in df.columns:
        df["rssi"] = df["ul_rssi"]
    else:
        df["rssi"] = None

# asegurar columnas
for col in ["dl_snr_db", "dl_rate"]:
    if col not in df.columns:
        df[col] = None

# seleccionar columnas finales
df = df[[
    "ts",
    "dl_snr_db",
    "dl_rate",
    "rssi"
]]

engine = create_engine(DB_URL)

# 🔥 IMPORTANTE: append (no replace)
df.to_sql("metricas_rf", engine, if_exists="append", index=False)

print("Datos RF insertados correctamente con RSSI")
