#!/usr/bin/env python3

import pandas as pd
import os

BASE = "/home/carlos/epmp_monitor"
INPUT = f"{BASE}/reportes/dataset_avanzado.csv"
OUTPUT = f"{BASE}/reportes/dataset_predictivo.csv"

if not os.path.exists(INPUT):
    print("No existe dataset_avanzado.csv")
    exit()

df = pd.read_csv(INPUT)

# asegurar datetime
df["ts"] = pd.to_datetime(df["ts"])

# ordenar
df = df.sort_values("ts").reset_index(drop=True)

# --- INICIALIZAR ---
df["estado_predictivo"] = "ESTABLE"
df["estado_predictivo_valor"] = 3

# --- DETECCIÓN DE CAÍDA POR VALORES ---
df.loc[df["dl_snr_db"] < 10, "estado_predictivo"] = "CAIDA"
df.loc[df["dl_snr_db"] < 10, "estado_predictivo_valor"] = 1

# --- DETECCIÓN DE RIESGO ---
df.loc[
    (df["dl_snr_db"] >= 10) & (df["dl_snr_db"] < 20),
    "estado_predictivo"
] = "RIESGO_PROXIMO"

df.loc[
    (df["dl_snr_db"] >= 10) & (df["dl_snr_db"] < 20),
    "estado_predictivo_valor"
] = 2

# --- DETECCIÓN DE SILENCIO (SIN DATOS REALES) ---
df["delta_t"] = df["ts"].diff().dt.total_seconds()

# si pasan más de 5 minutos sin datos → SIN_DATOS
df.loc[df["delta_t"] > 300, "estado_predictivo"] = "SIN_DATOS"
df.loc[df["delta_t"] > 300, "estado_predictivo_valor"] = 0

# --- LIMPIEZA ---
df = df.drop(columns=["delta_t"])

# --- GUARDAR ---
df.to_csv(OUTPUT, index=False)

print(f"ESTADO PREDICTIVO OK: {OUTPUT}")
print(df.tail(10))
