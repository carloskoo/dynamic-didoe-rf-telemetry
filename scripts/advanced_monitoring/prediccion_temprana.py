#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os

BASE = "/home/carlos/epmp_monitor"
INPUT = f"{BASE}/reportes/dataset_avanzado.csv"
OUTPUT = f"{BASE}/reportes/dataset_prediccion_temprana.csv"

if not os.path.exists(INPUT):
    print("No existe dataset_avanzado.csv")
    exit()

df = pd.read_csv(INPUT)

df["ts"] = pd.to_datetime(df["ts"])
df = df.sort_values("ts").reset_index(drop=True)

# ===============================
# FEATURE ENGINEERING
# ===============================

# Tendencia (pendiente)
df["snr_slope"] = df["dl_snr_db"].diff()

# Tendencia acumulada (ventana)
df["snr_slope_5"] = df["dl_snr_db"].diff(5)

# Volatilidad
df["snr_std_5"] = df["dl_snr_db"].rolling(5).std()

# Aceleración (segunda derivada)
df["snr_acc"] = df["snr_slope"].diff()

# ===============================
# DETECCIÓN TEMPRANA
# ===============================

def detectar_degradacion(row):
    score = 0

    # Caída sostenida
    if row["snr_slope_5"] < -3:
        score += 2

    # Caída fuerte reciente
    if row["snr_slope"] < -1:
        score += 2

    # Aceleración negativa
    if row["snr_acc"] < -0.5:
        score += 1

    # Alta variabilidad
    if row["snr_std_5"] > 2:
        score += 1

    return score

df["score_degradacion"] = df.apply(detectar_degradacion, axis=1)

# ===============================
# CLASIFICACIÓN
# ===============================

df["alerta_temprana"] = "NORMAL"

df.loc[df["score_degradacion"] >= 4, "alerta_temprana"] = "DEGRADACION_INMINENTE"
df.loc[(df["score_degradacion"] >= 2) & (df["score_degradacion"] < 4), "alerta_temprana"] = "DEGRADACION_INICIAL"

# ===============================
# NUMÉRICO PARA GRAFANA
# ===============================

df["alerta_valor"] = 0
df.loc[df["alerta_temprana"] == "DEGRADACION_INICIAL", "alerta_valor"] = 1
df.loc[df["alerta_temprana"] == "DEGRADACION_INMINENTE", "alerta_valor"] = 2

# ===============================
# GUARDAR
# ===============================

df.to_csv(OUTPUT, index=False)

print("PREDICCION TEMPRANA OK")
print(df[["ts","dl_snr_db","snr_slope","snr_std_5","alerta_temprana"]].tail(10))
